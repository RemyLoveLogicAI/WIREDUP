"""
AI Auto-Wiring System - Main Package
"""

__version__ = "1.0.0"
__author__ = "AI Auto-Wiring Team"
__license__ = "MIT"

from src.core.autowire import AutoWire, Scope, inject, get_autowire
from src.config import get_config_loader, get_config
from src.mcp import MCPProtocol
from src.ssh import SSHManager
from src.agents import SwarmOrchestrator, SwarmStrategy

__all__ = [
    'AutoWire',
    'Scope',
    'inject',
    'get_autowire',
    'get_config_loader',
    'get_config',
    'MCPProtocol',
    'SSHManager',
    'SwarmOrchestrator',
    'SwarmStrategy',
]
