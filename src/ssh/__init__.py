"""
SSH module for secure remote connections
"""

from .manager import (
    SSHManager,
    SSHConnectionPool,
    SSHCredentials,
    SSHConnection,
    SSHExecutionResult
)

__all__ = [
    'SSHManager',
    'SSHConnectionPool',
    'SSHCredentials',
    'SSHConnection',
    'SSHExecutionResult'
]
