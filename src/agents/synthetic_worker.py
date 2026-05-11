"""
Synthetic worker agents for orchestration CLI/load scenarios.
"""

import asyncio
from typing import Any, Dict, Optional, Sequence, Set

from .base_agent import AgentContext, BaseAgent


class SyntheticWorkerAgent(BaseAgent):
    """
    Configurable worker used by CLI swarm operations.

    Supported config keys:
    - delay_ms: artificial latency in milliseconds
    - failure_mode: never | always | first_attempt
    - fail_on_calls: list of call numbers to fail on (1-indexed)
    - result_payload: dictionary merged into success output
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self._calls = 0

    async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]:
        self._calls += 1
        delay_ms = self._to_positive_int(self.get_config("delay_ms", 0), default=0)
        if delay_ms > 0:
            await asyncio.sleep(delay_ms / 1000)

        failure_mode = str(self.get_config("failure_mode", "never")).strip().lower()
        fail_on_calls = self._to_call_set(self.get_config("fail_on_calls", []))

        if failure_mode == "always":
            raise RuntimeError(f"Synthetic worker '{self.name}' forced failure (always)")
        if failure_mode == "first_attempt" and self._calls == 1:
            raise RuntimeError(f"Synthetic worker '{self.name}' forced failure (first_attempt)")
        if self._calls in fail_on_calls:
            raise RuntimeError(f"Synthetic worker '{self.name}' forced failure on call {self._calls}")

        payload = self.get_config("result_payload", {})
        payload = payload if isinstance(payload, dict) else {}

        return {
            "success": True,
            "agent": self.name,
            "task": task,
            "call_count": self._calls,
            "correlation_id": context.metadata.get("correlation_id"),
            **payload,
        }

    @staticmethod
    def _to_positive_int(value: Any, *, default: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return parsed if parsed > 0 else 0

    @staticmethod
    def _to_call_set(value: Any) -> Set[int]:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            return set()
        parsed: Set[int] = set()
        for item in value:
            try:
                num = int(item)
            except (TypeError, ValueError):
                continue
            if num > 0:
                parsed.add(num)
        return parsed
