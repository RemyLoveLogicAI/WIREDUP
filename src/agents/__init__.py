"""
Agents module
"""

from .base_agent import BaseAgent, AgentContext
from .synthetic_worker import SyntheticWorkerAgent
from .swarm_orchestrator import SwarmOrchestrator, SwarmStrategy, SubAgentResult

__all__ = [
    'BaseAgent',
    'AgentContext',
    'SyntheticWorkerAgent',
    'SwarmOrchestrator',
    'SwarmStrategy',
    'SubAgentResult',
]
