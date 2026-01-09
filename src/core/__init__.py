"""
Core module for AI Auto-Wiring System
"""

from .autowire import AutoWire, Scope, inject, get_autowire
from .registry import ServiceRegistry, ComponentRegistry

__all__ = [
    'AutoWire',
    'Scope',
    'inject',
    'get_autowire',
    'ServiceRegistry',
    'ComponentRegistry'
]
