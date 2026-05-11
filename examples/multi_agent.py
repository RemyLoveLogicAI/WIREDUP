"""
Multi-Agent Swarm Example
Demonstrates mass orchestration with multiple sub-agents.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents import AgentContext, BaseAgent, SwarmOrchestrator, SwarmStrategy


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkerAgent(BaseAgent):
    """Simple worker agent for swarm demonstrations."""

    async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]:
        await asyncio.sleep(0.05)
        return {
            "success": True,
            "agent": self.name,
            "task": task,
            "session": context.session_id,
        }


class FlakyWorkerAgent(BaseAgent):
    """Agent that fails once before succeeding."""

    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self._calls = 0

    async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]:
        self._calls += 1
        if self._calls == 1:
            raise RuntimeError("Transient worker failure")
        await asyncio.sleep(0.02)
        return {
            "success": True,
            "agent": self.name,
            "task": task,
            "attempt": self._calls,
        }


async def main():
    print("🚀 Multi-Agent Swarm Example\n")

    orchestrator = SwarmOrchestrator(
        "swarm_controller",
        {
            "strategy": SwarmStrategy.PARALLEL.value,
            "max_concurrency": 4,
            "sub_agent_timeout": 5,
            "sub_agent_retries": 1,
        },
    )

    orchestrator.add_sub_agents(
        [
            WorkerAgent("worker_1"),
            WorkerAgent("worker_2"),
            WorkerAgent("worker_3"),
            FlakyWorkerAgent("flaky_worker"),
        ]
    )

    context = AgentContext(session_id="swarm_demo_session", user_id="demo_user")

    print(f"✅ Registered sub-agents: {', '.join(orchestrator.list_sub_agents())}\n")

    print("1) Single swarm operation")
    report = await orchestrator.execute_swarm("Analyze quarterly metrics", context)
    print(
        f"   success={report['success']} "
        f"successful_agents={report['successful_agents']} "
        f"failed_agents={report['failed_agents']}"
    )

    print("\n2) Mass swarm operation (multiple tasks)")
    mass_report = await orchestrator.execute_mass_swarm(
        tasks=[
            "Generate incident summary",
            "Review deployment status",
            "Validate backup integrity",
        ],
        context=context,
        parallel_tasks=True,
    )
    print(
        f"   success={mass_report['success']} "
        f"successful_tasks={mass_report['successful_tasks']} "
        f"failed_tasks={mass_report['failed_tasks']}"
    )

    print("\n✅ Example completed")


if __name__ == "__main__":
    asyncio.run(main())
