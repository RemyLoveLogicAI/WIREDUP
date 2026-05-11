"""
Swarm Orchestrator
Production-ready multi-sub-agent orchestration for mass operations.
"""

import asyncio
import copy
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from math import ceil
from time import perf_counter
from typing import Any, Callable, Dict, List, Optional, Sequence
from uuid import uuid4

from .base_agent import AgentContext, BaseAgent


logger = logging.getLogger(__name__)


class SwarmStrategy(Enum):
    """Execution strategy for sub-agents."""

    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"


@dataclass
class SubAgentResult:
    """Execution result for a single sub-agent."""

    agent: str
    success: bool
    output: Optional[Any]
    error: Optional[str]
    attempts: int
    timed_out: bool
    duration_ms: int
    operation_id: str
    correlation_id: str
    sub_operation_id: str
    attempt_errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return a serializable dictionary representation."""
        return asdict(self)


class SwarmOrchestrator(BaseAgent):
    """
    Coordinates many sub-agents with concurrency controls.

    Configuration keys:
    - strategy: parallel | sequential
    - max_concurrency: max in-flight sub-agent calls in parallel strategy
    - sub_agent_timeout: per-attempt timeout in seconds (0 or None disables)
    - sub_agent_retries: retry count for failed sub-agent execution
    - fail_fast: stop early on first hard failure
    - isolate_context: copy context per sub-agent to prevent shared-state races
    - max_task_concurrency: max in-flight tasks for execute_mass_swarm
    - metrics_logging: emit structured metric logs
    - metrics_history_limit: max in-memory metric records
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self._sub_agents: Dict[str, BaseAgent] = {}

        self._strategy = self._resolve_strategy(self.get_config("strategy", SwarmStrategy.PARALLEL.value))
        self._max_concurrency = max(1, self._coerce_int(self.get_config("max_concurrency", 8), default=8))
        self._sub_agent_timeout = self._coerce_timeout(self.get_config("sub_agent_timeout", 30))
        self._sub_agent_retries = max(0, self._coerce_int(self.get_config("sub_agent_retries", 0), default=0))
        self._fail_fast = self._coerce_bool(self.get_config("fail_fast", False))
        self._isolate_context = self._coerce_bool(self.get_config("isolate_context", True))
        self._max_task_concurrency = max(
            1, self._coerce_int(self.get_config("max_task_concurrency", 4), default=4)
        )
        self._metrics_logging_enabled = self._coerce_bool(self.get_config("metrics_logging", True))
        self._metrics_history_limit = max(
            1, self._coerce_int(self.get_config("metrics_history_limit", 200), default=200)
        )
        self._metrics_hooks: List[Callable[[Dict[str, Any]], None]] = []
        self._metrics_history: List[Dict[str, Any]] = []

        if self._metrics_logging_enabled:
            self.register_metrics_hook(self._default_metrics_hook)

    def add_sub_agent(self, agent: BaseAgent) -> None:
        """Register a sub-agent in the swarm."""
        if agent.name == self.name:
            raise ValueError("Orchestrator cannot register itself as a sub-agent")

        self._sub_agents[agent.name] = agent
        self.log_info(f"Added sub-agent: {agent.name}")

    def add_sub_agents(self, agents: Sequence[BaseAgent]) -> None:
        """Register multiple sub-agents."""
        for agent in agents:
            self.add_sub_agent(agent)

    def remove_sub_agent(self, agent_name: str) -> bool:
        """Remove a sub-agent by name."""
        existed = agent_name in self._sub_agents
        self._sub_agents.pop(agent_name, None)
        return existed

    def list_sub_agents(self) -> List[str]:
        """List registered sub-agent names."""
        return list(self._sub_agents.keys())

    def register_metrics_hook(self, hook: Callable[[Dict[str, Any]], None]) -> "SwarmOrchestrator":
        """Register callback invoked for each metrics payload."""
        self._metrics_hooks.append(hook)
        return self

    def get_metrics_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return recorded swarm metrics."""
        if limit is None:
            return [dict(item) for item in self._metrics_history]
        return [dict(item) for item in self._metrics_history[-max(0, limit) :]]

    async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]:
        """
        Broadcast a task to all registered sub-agents.
        """
        return await self.execute_swarm(task=task, context=context)

    async def execute_swarm(
        self,
        task: str,
        context: AgentContext,
        *,
        target_agents: Optional[Sequence[str]] = None,
        sub_tasks: Optional[Dict[str, str]] = None,
        strategy: Optional[Any] = None,
        max_concurrency: Optional[int] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        fail_fast: Optional[bool] = None,
        correlation_id: Optional[str] = None,
        operation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute one orchestrated swarm operation.

        Args:
            task: Default task text for all sub-agents
            context: Shared parent context
            target_agents: Optional subset of sub-agent names
            sub_tasks: Optional per-agent task override map
            strategy: Optional execution strategy override
            max_concurrency: Optional parallel concurrency override
            timeout: Optional timeout override in seconds
            retries: Optional retries override
            fail_fast: Optional fail-fast override
            correlation_id: Optional trace correlation ID
            operation_id: Optional explicit swarm operation ID
        """
        started_at = datetime.now(timezone.utc).isoformat()
        operation_start = perf_counter()
        resolved_operation_id = operation_id or self._new_id("swarm")
        resolved_correlation_id = (
            correlation_id
            or context.metadata.get("correlation_id")
            or self._new_id("corr")
        )
        context.metadata.setdefault("correlation_id", resolved_correlation_id)

        strategy_value = self._strategy if strategy is None else self._resolve_strategy(strategy)

        self._emit_structured_log(
            "swarm_operation_started",
            {
                "operation_id": resolved_operation_id,
                "correlation_id": resolved_correlation_id,
                "orchestrator": self.name,
                "strategy": strategy_value.value,
                "task": task,
                "requested_agents": list(target_agents) if target_agents else self.list_sub_agents(),
            },
        )

        if not self._sub_agents:
            report = self._build_report(
                task=task,
                strategy=strategy_value,
                started_at=started_at,
                duration_ms=0,
                results=[],
                operation_id=resolved_operation_id,
                correlation_id=resolved_correlation_id,
                note="No sub-agents registered",
            )
            report["metrics"] = self._build_metrics(report=report, results=[])
            self._publish_metrics(report["metrics"])
            return report

        effective_timeout = self._sub_agent_timeout if timeout is None else self._coerce_timeout(timeout)
        effective_retries = self._sub_agent_retries if retries is None else max(0, int(retries))
        effective_fail_fast = self._fail_fast if fail_fast is None else bool(fail_fast)
        effective_concurrency = self._max_concurrency if max_concurrency is None else max(1, int(max_concurrency))

        agent_names = list(target_agents) if target_agents is not None else self.list_sub_agents()
        unknown_agents = [name for name in agent_names if name not in self._sub_agents]
        if unknown_agents:
            raise ValueError(f"Unknown sub-agent(s): {', '.join(unknown_agents)}")

        task_map = {name: (sub_tasks.get(name) if sub_tasks and name in sub_tasks else task) for name in agent_names}

        if strategy_value == SwarmStrategy.SEQUENTIAL:
            results = await self._run_sequential(
                agent_names=agent_names,
                task_map=task_map,
                context=context,
                timeout=effective_timeout,
                retries=effective_retries,
                fail_fast=effective_fail_fast,
                operation_id=resolved_operation_id,
                correlation_id=resolved_correlation_id,
            )
        else:
            results = await self._run_parallel(
                agent_names=agent_names,
                task_map=task_map,
                context=context,
                timeout=effective_timeout,
                retries=effective_retries,
                fail_fast=effective_fail_fast,
                max_concurrency=effective_concurrency,
                operation_id=resolved_operation_id,
                correlation_id=resolved_correlation_id,
            )

        duration_ms = int((perf_counter() - operation_start) * 1000)
        report = self._build_report(
            task=task,
            strategy=strategy_value,
            started_at=started_at,
            duration_ms=duration_ms,
            results=results,
            operation_id=resolved_operation_id,
            correlation_id=resolved_correlation_id,
        )
        report["metrics"] = self._build_metrics(report=report, results=results)
        self._publish_metrics(report["metrics"])

        self._append_limited(
            context.state.setdefault("swarm_history", []),
            {
                "operation_id": resolved_operation_id,
                "correlation_id": resolved_correlation_id,
                "orchestrator": self.name,
                "task": task,
                "success": report["success"],
                "successful_agents": report["successful_agents"],
                "failed_agents": report["failed_agents"],
                "duration_ms": report["duration_ms"],
                "timestamp": report["finished_at"],
            },
            self._metrics_history_limit,
        )
        self._append_limited(
            context.state.setdefault("swarm_metrics", []),
            report["metrics"],
            self._metrics_history_limit,
        )
        self._emit_structured_log(
            "swarm_operation_completed",
            {
                "operation_id": resolved_operation_id,
                "correlation_id": resolved_correlation_id,
                "success": report["success"],
                "duration_ms": report["duration_ms"],
                "successful_agents": report["successful_agents"],
                "failed_agents": report["failed_agents"],
            },
        )

        return report

    async def execute_mass_swarm(
        self,
        tasks: Sequence[str],
        context: AgentContext,
        *,
        target_agents: Optional[Sequence[str]] = None,
        strategy: Optional[Any] = None,
        max_concurrency: Optional[int] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        fail_fast: Optional[bool] = None,
        parallel_tasks: bool = True,
        correlation_id: Optional[str] = None,
        operation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a batch of swarm operations (mass mode).
        """
        started_at = datetime.now(timezone.utc).isoformat()
        operation_start = perf_counter()
        resolved_operation_id = operation_id or self._new_id("mass_swarm")
        resolved_correlation_id = (
            correlation_id
            or context.metadata.get("correlation_id")
            or self._new_id("corr")
        )
        context.metadata.setdefault("correlation_id", resolved_correlation_id)

        task_list = list(tasks)
        if not task_list:
            report = {
                "success": True,
                "agent": self.name,
                "mode": "mass_swarm",
                "operation_id": resolved_operation_id,
                "correlation_id": resolved_correlation_id,
                "started_at": started_at,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "duration_ms": 0,
                "total_tasks": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "operations": [],
            }
            report["metrics"] = self._build_mass_metrics(report)
            self._publish_metrics(report["metrics"])
            return report

        self._emit_structured_log(
            "mass_swarm_started",
            {
                "operation_id": resolved_operation_id,
                "correlation_id": resolved_correlation_id,
                "task_count": len(task_list),
                "parallel_tasks": parallel_tasks,
            },
        )

        async def run_single(index: int, single_task: str) -> Dict[str, Any]:
            return await self.execute_swarm(
                task=single_task,
                context=context,
                target_agents=target_agents,
                strategy=strategy,
                max_concurrency=max_concurrency,
                timeout=timeout,
                retries=retries,
                fail_fast=fail_fast,
                correlation_id=resolved_correlation_id,
                operation_id=f"{resolved_operation_id}_task_{index + 1}",
            )

        operations: List[Dict[str, Any]] = []

        if parallel_tasks:
            task_limit = min(self._max_task_concurrency, len(task_list))
            semaphore = asyncio.Semaphore(max(1, task_limit))

            async def run_with_limit(index: int, single_task: str) -> Dict[str, Any]:
                async with semaphore:
                    return await run_single(index, single_task)

            futures = [
                asyncio.create_task(run_with_limit(index, single_task))
                for index, single_task in enumerate(task_list)
            ]
            operations = list(await asyncio.gather(*futures))
        else:
            for index, single_task in enumerate(task_list):
                operations.append(await run_single(index, single_task))

        successful_tasks = sum(1 for operation in operations if operation.get("success"))
        failed_tasks = len(operations) - successful_tasks

        report = {
            "success": failed_tasks == 0,
            "agent": self.name,
            "mode": "mass_swarm",
            "operation_id": resolved_operation_id,
            "correlation_id": resolved_correlation_id,
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "duration_ms": int((perf_counter() - operation_start) * 1000),
            "total_tasks": len(task_list),
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "operations": operations,
        }
        report["metrics"] = self._build_mass_metrics(report)
        self._publish_metrics(report["metrics"])
        self._emit_structured_log(
            "mass_swarm_completed",
            {
                "operation_id": resolved_operation_id,
                "correlation_id": resolved_correlation_id,
                "success": report["success"],
                "task_count": report["total_tasks"],
                "duration_ms": report["duration_ms"],
                "failed_tasks": report["failed_tasks"],
            },
        )
        return report

    async def _run_sequential(
        self,
        *,
        agent_names: Sequence[str],
        task_map: Dict[str, str],
        context: AgentContext,
        timeout: Optional[float],
        retries: int,
        fail_fast: bool,
        operation_id: str,
        correlation_id: str,
    ) -> List[SubAgentResult]:
        results: List[SubAgentResult] = []

        for index, agent_name in enumerate(agent_names):
            result = await self._execute_single_agent(
                agent_name=agent_name,
                task=task_map[agent_name],
                context=context,
                timeout=timeout,
                retries=retries,
                operation_id=operation_id,
                correlation_id=correlation_id,
            )
            results.append(result)

            if fail_fast and not result.success:
                for remaining_agent in agent_names[index + 1 :]:
                    results.append(
                        SubAgentResult(
                            agent=remaining_agent,
                            success=False,
                            output=None,
                            error="Skipped due to fail_fast policy",
                            attempts=0,
                            timed_out=False,
                            duration_ms=0,
                            operation_id=operation_id,
                            correlation_id=correlation_id,
                            sub_operation_id=f"{operation_id}:{remaining_agent}",
                        )
                    )
                break

        return results

    async def _run_parallel(
        self,
        *,
        agent_names: Sequence[str],
        task_map: Dict[str, str],
        context: AgentContext,
        timeout: Optional[float],
        retries: int,
        fail_fast: bool,
        max_concurrency: int,
        operation_id: str,
        correlation_id: str,
    ) -> List[SubAgentResult]:
        semaphore = asyncio.Semaphore(max_concurrency)
        pending: Dict[str, asyncio.Task] = {}
        completed: Dict[str, SubAgentResult] = {}

        async def run_agent(agent_name: str) -> SubAgentResult:
            async with semaphore:
                return await self._execute_single_agent(
                    agent_name=agent_name,
                    task=task_map[agent_name],
                    context=context,
                    timeout=timeout,
                    retries=retries,
                    operation_id=operation_id,
                    correlation_id=correlation_id,
                )

        for agent_name in agent_names:
            pending[agent_name] = asyncio.create_task(run_agent(agent_name))

        try:
            for finished in asyncio.as_completed(pending.values()):
                result = await finished
                completed[result.agent] = result

                if fail_fast and not result.success:
                    for task in pending.values():
                        if not task.done():
                            task.cancel()
                    break
        finally:
            await asyncio.gather(*pending.values(), return_exceptions=True)

        if fail_fast and len(completed) < len(agent_names):
            for agent_name in agent_names:
                if agent_name not in completed:
                    completed[agent_name] = SubAgentResult(
                        agent=agent_name,
                        success=False,
                        output=None,
                        error="Cancelled due to fail_fast policy",
                        attempts=0,
                        timed_out=False,
                        duration_ms=0,
                        operation_id=operation_id,
                        correlation_id=correlation_id,
                        sub_operation_id=f"{operation_id}:{agent_name}",
                    )

        ordered_results = [completed[name] for name in agent_names if name in completed]
        return ordered_results

    async def _execute_single_agent(
        self,
        *,
        agent_name: str,
        task: str,
        context: AgentContext,
        timeout: Optional[float],
        retries: int,
        operation_id: str,
        correlation_id: str,
    ) -> SubAgentResult:
        agent = self._sub_agents[agent_name]
        started_at = perf_counter()
        attempts = 0
        timed_out = False
        last_error: Optional[str] = None
        attempt_errors: List[str] = []
        sub_operation_id = f"{operation_id}:{agent_name}"

        while attempts <= retries:
            attempts += 1
            local_context = self._create_sub_context(
                parent=context,
                sub_agent_name=agent_name,
                operation_id=operation_id,
                correlation_id=correlation_id,
                sub_operation_id=sub_operation_id,
            )

            try:
                execution = agent.execute(task, local_context)
                if timeout is not None:
                    output = await asyncio.wait_for(execution, timeout=timeout)
                else:
                    output = await execution

                return SubAgentResult(
                    agent=agent_name,
                    success=True,
                    output=output,
                    error=None,
                    attempts=attempts,
                    timed_out=False,
                    duration_ms=int((perf_counter() - started_at) * 1000),
                    operation_id=operation_id,
                    correlation_id=correlation_id,
                    sub_operation_id=sub_operation_id,
                    attempt_errors=attempt_errors,
                )
            except asyncio.TimeoutError:
                timed_out = True
                timeout_text = "none" if timeout is None else str(timeout)
                last_error = f"Timed out after {timeout_text}s"
                attempt_errors.append(last_error)
                self.log_warning(f"Sub-agent '{agent_name}' timeout on attempt {attempts}")
            except Exception as exc:  # pragma: no cover - safeguard path
                last_error = str(exc)
                attempt_errors.append(last_error)
                self.log_warning(f"Sub-agent '{agent_name}' failed on attempt {attempts}: {exc}")

        return SubAgentResult(
            agent=agent_name,
            success=False,
            output=None,
            error=last_error or "Unknown execution error",
            attempts=attempts,
            timed_out=timed_out,
            duration_ms=int((perf_counter() - started_at) * 1000),
            operation_id=operation_id,
            correlation_id=correlation_id,
            sub_operation_id=sub_operation_id,
            attempt_errors=attempt_errors,
        )

    def _create_sub_context(
        self,
        *,
        parent: AgentContext,
        sub_agent_name: str,
        operation_id: str,
        correlation_id: str,
        sub_operation_id: str,
    ) -> AgentContext:
        """Create a child context for a sub-agent execution."""
        if not self._isolate_context:
            parent.metadata["swarm_parent"] = self.name
            parent.metadata["sub_agent"] = sub_agent_name
            parent.metadata["operation_id"] = operation_id
            parent.metadata["sub_operation_id"] = sub_operation_id
            parent.metadata["correlation_id"] = correlation_id
            return parent

        child_metadata = dict(parent.metadata)
        child_metadata["swarm_parent"] = self.name
        child_metadata["sub_agent"] = sub_agent_name
        child_metadata["operation_id"] = operation_id
        child_metadata["sub_operation_id"] = sub_operation_id
        child_metadata["correlation_id"] = correlation_id

        return AgentContext(
            session_id=parent.session_id,
            user_id=parent.user_id,
            metadata=child_metadata,
            state=copy.deepcopy(parent.state),
        )

    def _build_report(
        self,
        *,
        task: str,
        strategy: SwarmStrategy,
        started_at: str,
        duration_ms: int,
        results: Sequence[SubAgentResult],
        operation_id: str,
        correlation_id: str,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        successful_agents = sum(1 for result in results if result.success)
        failed_agents = len(results) - successful_agents

        return {
            "success": failed_agents == 0,
            "agent": self.name,
            "operation_id": operation_id,
            "correlation_id": correlation_id,
            "task": task,
            "strategy": strategy.value,
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "duration_ms": duration_ms,
            "total_agents": len(results),
            "successful_agents": successful_agents,
            "failed_agents": failed_agents,
            "results": [result.to_dict() for result in results],
            "summary": f"Swarm executed {len(results)} agents: {successful_agents} succeeded, {failed_agents} failed",
            "note": note,
        }

    def _build_metrics(self, *, report: Dict[str, Any], results: Sequence[SubAgentResult]) -> Dict[str, Any]:
        duration_values = [result.duration_ms for result in results]
        retries_used = sum(max(0, result.attempts - 1) for result in results)
        timeout_count = sum(1 for result in results if result.timed_out)
        total_agents = report.get("total_agents", len(results))
        successful_agents = report.get("successful_agents", 0)
        failed_agents = report.get("failed_agents", 0)

        success_rate = (successful_agents / total_agents) if total_agents else 1.0
        failure_rate = (failed_agents / total_agents) if total_agents else 0.0

        return {
            "event": "swarm_operation",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "orchestrator": self.name,
            "operation_id": report["operation_id"],
            "correlation_id": report["correlation_id"],
            "strategy": report["strategy"],
            "duration_ms": report["duration_ms"],
            "total_agents": total_agents,
            "successful_agents": successful_agents,
            "failed_agents": failed_agents,
            "success_rate": round(success_rate, 4),
            "failure_rate": round(failure_rate, 4),
            "timeout_count": timeout_count,
            "retries_used": retries_used,
            "attempts_total": sum(result.attempts for result in results),
            "sub_agent_duration_p95_ms": self._percentile(duration_values, 95),
        }

    def _build_mass_metrics(self, report: Dict[str, Any]) -> Dict[str, Any]:
        operation_durations = [operation.get("duration_ms", 0) for operation in report.get("operations", [])]
        total_tasks = report.get("total_tasks", 0)
        successful_tasks = report.get("successful_tasks", 0)
        failed_tasks = report.get("failed_tasks", 0)
        success_rate = (successful_tasks / total_tasks) if total_tasks else 1.0
        failure_rate = (failed_tasks / total_tasks) if total_tasks else 0.0

        return {
            "event": "mass_swarm_operation",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "orchestrator": self.name,
            "operation_id": report["operation_id"],
            "correlation_id": report["correlation_id"],
            "duration_ms": report["duration_ms"],
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": round(success_rate, 4),
            "failure_rate": round(failure_rate, 4),
            "operation_duration_p95_ms": self._percentile(operation_durations, 95),
        }

    def _publish_metrics(self, metrics: Dict[str, Any]) -> None:
        self._append_limited(self._metrics_history, dict(metrics), self._metrics_history_limit)
        for hook in self._metrics_hooks:
            try:
                hook(dict(metrics))
            except Exception as exc:  # pragma: no cover - defensive hook safety
                logger.error(f"Metrics hook error: {exc}")

    def _default_metrics_hook(self, metrics: Dict[str, Any]) -> None:
        self._emit_structured_log("swarm_metrics", metrics)

    def _emit_structured_log(self, event: str, payload: Dict[str, Any]) -> None:
        data = {"event": event, **payload}
        logger.info(json.dumps(data, sort_keys=True, default=str))

    @staticmethod
    def _append_limited(target: List[Any], item: Any, limit: int) -> None:
        target.append(item)
        if len(target) > limit:
            del target[: len(target) - limit]

    @staticmethod
    def _new_id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:12]}"

    @staticmethod
    def _percentile(values: Sequence[int], percentile: int) -> int:
        if not values:
            return 0
        ordered = sorted(values)
        rank = max(1, ceil((percentile / 100) * len(ordered)))
        index = min(len(ordered) - 1, rank - 1)
        return int(ordered[index])

    @staticmethod
    def _resolve_strategy(strategy: Any) -> SwarmStrategy:
        if isinstance(strategy, SwarmStrategy):
            return strategy

        if isinstance(strategy, str):
            lowered = strategy.strip().lower()
            if lowered == SwarmStrategy.SEQUENTIAL.value:
                return SwarmStrategy.SEQUENTIAL

        return SwarmStrategy.PARALLEL

    @staticmethod
    def _coerce_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

    @staticmethod
    def _coerce_int(value: Any, *, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _coerce_timeout(value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            timeout = float(value)
        except (TypeError, ValueError):
            return None
        return timeout if timeout > 0 else None
