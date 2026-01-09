"""
Base Agent Implementation
Foundation for all AI agents in the system.
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """Execution context for agents"""
    session_id: str
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class BaseAgent(ABC):
    """
    Base class for all AI agents.
    
    Provides common functionality:
    - Logging
    - Configuration management
    - Skill management
    - State handling
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self._skills: Dict[str, Any] = {}
        self.logger = logging.getLogger(f"agent.{name}")
        
        self.logger.info(f"Agent {name} initialized")
    
    @abstractmethod
    async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]:
        """
        Execute agent task.
        
        Args:
            task: Task description or command
            context: Execution context
        
        Returns:
            Execution result dictionary
        """
        pass
    
    def add_skill(self, skill_name: str, skill):
        """Add a skill to the agent"""
        self._skills[skill_name] = skill
        self.logger.debug(f"Added skill: {skill_name}")
    
    def has_skill(self, skill_name: str) -> bool:
        """Check if agent has a skill"""
        return skill_name in self._skills
    
    async def use_skill(self, skill_name: str, **kwargs) -> Any:
        """Use a registered skill"""
        if not self.has_skill(skill_name):
            raise ValueError(f"Skill '{skill_name}' not available")
        
        skill = self._skills[skill_name]
        
        if hasattr(skill, 'execute'):
            return await skill.execute(**kwargs)
        elif callable(skill):
            return await skill(**kwargs)
        else:
            raise TypeError(f"Skill '{skill_name}' is not callable")
    
    def log_info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def log_warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def log_error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def log_debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set_config(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
