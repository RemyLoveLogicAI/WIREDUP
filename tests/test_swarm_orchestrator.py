"""
Tests for production swarm orchestration.
"""

import asyncio
from typing import Any, Dict

import pytest

from src.agents import AgentContext, BaseAgent, SwarmOrchestrator, SwarmStrategy


class EchoWorker(BaseAgent):
    """Sub-agent that echoes task metadata."""

    def __init__(self, name: str, delay: float = 0.01):
        super().__init__(name)
        self.delay = delay
        self.calls = 0

    async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]:
        self.calls += 1
        await asyncio.sleep(self.delay)
        return {
            "success": True,
            "agent": self.name,
            "task": task,
            "session_id": context.session_id,
        }


class FlakyWorker(BaseAgent):
    """Fails once, then succeeds."""

    def __init__(self, name: str):
        super().__init__(name)
        self.calls = 0

    async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("transient failure")
        return {
            "success": True,
            "agent": self.name,
            "task": task,
            "calls": self.calls,
        }


class AlwaysFailWorker(BaseAgent):
    """Always fails execution."""

    def __init__(self, name: str):
        super().__init__(name)
        self.calls = 0

    async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]:
        self.calls += 1
        raise RuntimeError("forced failure")


@pytest.mark.asyncio
async def test_parallel_swarm_executes_all_sub_agents():
    orchestrator = SwarmOrchestrator(
        "orchestrator",
        {
            "strategy": SwarmStrategy.PARALLEL.value,
            "max_concurrency": 6,
        },
    )

    workers = [EchoWorker(f"worker_{index}") for index in range(12)]
    orchestrator.add_sub_agents(workers)

    report = await orchestrator.execute_swarm("parallel-task", AgentContext(session_id="parallel"))

    assert report["success"] is True
    assert report["total_agents"] == 12
    assert report["successful_agents"] == 12
    assert report["failed_agents"] == 0
    assert all(result["success"] is True for result in report["results"])


@pytest.mark.asyncio
async def test_target_agents_and_sub_task_overrides():
    orchestrator = SwarmOrchestrator("orchestrator")
    worker_a = EchoWorker("worker_a")
    worker_b = EchoWorker("worker_b")
    orchestrator.add_sub_agents([worker_a, worker_b])

    report = await orchestrator.execute_swarm(
        "default-task",
        AgentContext(session_id="targeted"),
        target_agents=["worker_a"],
        sub_tasks={"worker_a": "custom-task-for-a", "worker_b": "custom-task-for-b"},
    )

    assert report["total_agents"] == 1
    assert report["results"][0]["agent"] == "worker_a"
    assert report["results"][0]["output"]["task"] == "custom-task-for-a"
    assert worker_a.calls == 1
    assert worker_b.calls == 0


@pytest.mark.asyncio
async def test_retry_policy_recovers_flaky_worker():
    orchestrator = SwarmOrchestrator(
        "orchestrator",
        {
            "sub_agent_retries": 1,
            "strategy": SwarmStrategy.SEQUENTIAL.value,
        },
    )
    flaky = FlakyWorker("flaky")
    orchestrator.add_sub_agent(flaky)

    report = await orchestrator.execute_swarm("retry-task", AgentContext(session_id="retry"))

    assert report["success"] is True
    assert report["results"][0]["success"] is True
    assert report["results"][0]["attempts"] == 2
    assert flaky.calls == 2


@pytest.mark.asyncio
async def test_timeout_marks_sub_agent_failure():
    orchestrator = SwarmOrchestrator(
        "orchestrator",
        {
            "sub_agent_timeout": 0.01,
            "sub_agent_retries": 0,
        },
    )
    orchestrator.add_sub_agent(EchoWorker("slow_worker", delay=0.05))

    report = await orchestrator.execute_swarm("timeout-task", AgentContext(session_id="timeout"))
    result = report["results"][0]

    assert report["success"] is False
    assert report["failed_agents"] == 1
    assert result["success"] is False
    assert result["timed_out"] is True
    assert "Timed out after" in result["error"]


@pytest.mark.asyncio
async def test_fail_fast_sequential_skips_remaining_agents():
    orchestrator = SwarmOrchestrator(
        "orchestrator",
        {
            "strategy": SwarmStrategy.SEQUENTIAL.value,
            "fail_fast": True,
        },
    )

    failing_worker = AlwaysFailWorker("failing_worker")
    skipped_worker = EchoWorker("should_be_skipped")

    orchestrator.add_sub_agent(failing_worker)
    orchestrator.add_sub_agent(skipped_worker)

    report = await orchestrator.execute_swarm("fail-fast-task", AgentContext(session_id="fail-fast"))

    assert report["success"] is False
    assert report["total_agents"] == 2
    assert report["results"][0]["agent"] == "failing_worker"
    assert report["results"][0]["success"] is False
    assert report["results"][1]["agent"] == "should_be_skipped"
    assert report["results"][1]["attempts"] == 0
    assert "Skipped due to fail_fast policy" in report["results"][1]["error"]
    assert skipped_worker.calls == 0


@pytest.mark.asyncio
async def test_execute_mass_swarm_runs_multiple_operations():
    orchestrator = SwarmOrchestrator(
        "orchestrator",
        {
            "max_task_concurrency": 3,
            "max_concurrency": 4,
        },
    )
    orchestrator.add_sub_agents([EchoWorker("w1"), EchoWorker("w2"), EchoWorker("w3")])

    context = AgentContext(session_id="mass")
    report = await orchestrator.execute_mass_swarm(
        tasks=["task-1", "task-2", "task-3", "task-4"],
        context=context,
        parallel_tasks=True,
    )

    assert report["success"] is True
    assert report["total_tasks"] == 4
    assert report["successful_tasks"] == 4
    assert report["failed_tasks"] == 0
    assert len(report["operations"]) == 4
    assert all(operation["total_agents"] == 3 for operation in report["operations"])
    assert len(context.state["swarm_history"]) == 4
