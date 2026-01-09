"""
Advanced Environment Configuration System
Multi-source configuration with validation, encryption, and hot-reloading.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import re
from datetime import datetime
import threading


logger = logging.getLogger(__name__)


class ConfigSource(Enum):
    """Configuration source types"""
    ENV_FILE = "env_file"
    ENVIRONMENT = "environment"
    JSON_FILE = "json_file"
    YAML_FILE = "yaml_file"
    COMMAND_LINE = "command_line"
    REMOTE = "remote"


class ValidationType(Enum):
    """Configuration validation types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    EMAIL = "email"
    URL = "url"
    PATH = "path"
    IP = "ip"
    PORT = "port"


@dataclass
class ConfigRule:
    """Validation rule for configuration parameter"""
    name: str
    validation_type: ValidationType
    required: bool = False
    default: Any = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    choices: Optional[List[Any]] = None
    description: str = ""
    sensitive: bool = False
    environment_var: Optional[str] = None


@dataclass
class ConfigValue:
    """Configuration value with metadata"""
    key: str
    value: Any
    source: ConfigSource
    timestamp: datetime = field(default_factory=datetime.now)
    validated: bool = False


class ConfigValidationError(Exception):
    """Raised when configuration validation fails"""
    pass


class EnvManager:
    """
    Advanced Environment Configuration Manager.
    
    Features:
    - Multi-source configuration loading
    - Validation with type checking
    - Sensitive data masking
    - Hot-reloading support
    - Environment-specific configs
    - Hierarchical configuration override
    """
    
    def __init__(
        self,
        env: str = "development",
        config_dir: Optional[Path] = None,
        auto_load: bool = True
    ):
        self.env = env
        self.config_dir = config_dir or Path.cwd()
        self._config: Dict[str, ConfigValue] = {}
        self._rules: Dict[str, ConfigRule] = {}
        self._watchers: List[Callable[[str, Any], None]] = []
        self._lock = threading.RLock()
        
        logger.info(f"EnvManager initialized (env={env})")
        
        if auto_load:
            self.load_all()
    
    def add_rule(self, rule: ConfigRule) -> 'EnvManager':
        """Add a validation rule"""
        with self._lock:
            self._rules[rule.name] = rule
            logger.debug(f"Added validation rule: {rule.name}")
            return self
    
    def add_rules(self, rules: List[ConfigRule]) -> 'EnvManager':
        """Add multiple validation rules"""
        for rule in rules:
            self.add_rule(rule)
        return self
    
    def load_env_file(self, file_path: Optional[Path] = None) -> 'EnvManager':
        """
        Load configuration from .env file.
        
        Supports:
        - KEY=value
        - Comments (# or //)
        - Multiline values with quotes
        - Variable expansion ${VAR}
        """
        with self._lock:
            if file_path is None:
                # Try multiple .env file locations
                env_files = [
                    self.config_dir / f".env.{self.env}",
                    self.config_dir / ".env.local",
                    self.config_dir / ".env",
                ]
                
                for env_file in env_files:
                    if env_file.exists():
                        file_path = env_file
                        break
            
            if file_path is None or not file_path.exists():
                logger.warning(f"No .env file found")
                return self
            
            logger.info(f"Loading .env file: {file_path}")
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse .env file
            for line in content.splitlines():
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#') or line.startswith('//'):
                    continue
                
                # Parse KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    # Variable expansion
                    value = self._expand_variables(value)
                    
                    self._set_value(key, value, ConfigSource.ENV_FILE)
            
            return self
    
    def load_environment(self) -> 'EnvManager':
        """Load configuration from environment variables"""
        with self._lock:
            logger.info("Loading environment variables")
            
            for key, value in os.environ.items():
                self._set_value(key, value, ConfigSource.ENVIRONMENT)
            
            return self
    
    def load_json(self, file_path: Path) -> 'EnvManager':
        """Load configuration from JSON file"""
        with self._lock:
            if not file_path.exists():
                logger.warning(f"JSON file not found: {file_path}")
                return self
            
            logger.info(f"Loading JSON config: {file_path}")
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            self._load_dict(data, ConfigSource.JSON_FILE)
            
            return self
    
    def load_dict(self, data: Dict[str, Any], source: ConfigSource = ConfigSource.COMMAND_LINE) -> 'EnvManager':
        """Load configuration from dictionary"""
        with self._lock:
            self._load_dict(data, source)
            return self
    
    def load_all(self) -> 'EnvManager':
        """Load configuration from all sources in priority order"""
        with self._lock:
            # 1. Load base .env file
            self.load_env_file()
            
            # 2. Load environment-specific JSON if exists
            json_file = self.config_dir / f"config.{self.env}.json"
            if json_file.exists():
                self.load_json(json_file)
            
            # 3. Override with environment variables
            self.load_environment()
            
            logger.info("Configuration loaded from all sources")
            
            return self
    
    def get(self, key: str, default: Any = None, required: bool = False) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found
            required: Raise error if not found
        
        Returns:
            Configuration value
        """
        with self._lock:
            config_value = self._config.get(key)
            
            if config_value is None:
                if required:
                    raise ConfigValidationError(f"Required configuration '{key}' not found")
                return default
            
            return config_value.value
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value"""
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get float configuration value"""
        value = self.get(key, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value"""
        value = self.get(key, default)
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', '1', 'on')
        
        return bool(value)
    
    def get_list(self, key: str, default: Optional[List] = None, separator: str = ',') -> List:
        """Get list configuration value"""
        value = self.get(key, default)
        
        if isinstance(value, list):
            return value
        
        if isinstance(value, str):
            return [item.strip() for item in value.split(separator)]
        
        return default or []
    
    def set(self, key: str, value: Any, source: ConfigSource = ConfigSource.COMMAND_LINE) -> 'EnvManager':
        """Set configuration value"""
        with self._lock:
            self._set_value(key, value, source)
            return self
    
    def validate(self) -> bool:
        """
        Validate all configuration values against rules.
        
        Returns:
            True if validation passes
        
        Raises:
            ConfigValidationError: If validation fails
        """
        with self._lock:
            errors = []
            
            # Check required values
            for rule_name, rule in self._rules.items():
                if rule.required and rule_name not in self._config:
                    if rule.default is not None:
                        self._set_value(rule_name, rule.default, ConfigSource.COMMAND_LINE)
                    else:
                        errors.append(f"Required configuration '{rule_name}' is missing")
            
            # Validate existing values
            for key, config_value in self._config.items():
                rule = self._rules.get(key)
                if rule:
                    try:
                        self._validate_value(config_value.value, rule)
                        config_value.validated = True
                    except ConfigValidationError as e:
                        errors.append(str(e))
            
            if errors:
                raise ConfigValidationError('\n'.join(errors))
            
            logger.info("Configuration validation passed")
            return True
    
    def watch(self, callback: Callable[[str, Any], None]) -> 'EnvManager':
        """Add a watcher callback for configuration changes"""
        with self._lock:
            self._watchers.append(callback)
            return self
    
    def to_dict(self, mask_sensitive: bool = True) -> Dict[str, Any]:
        """Export configuration as dictionary"""
        with self._lock:
            result = {}
            
            for key, config_value in self._config.items():
                rule = self._rules.get(key)
                
                if mask_sensitive and rule and rule.sensitive:
                    result[key] = "***MASKED***"
                else:
                    result[key] = config_value.value
            
            return result
    
    def get_info(self) -> Dict[str, Dict]:
        """Get detailed information about configuration"""
        with self._lock:
            info = {}
            
            for key, config_value in self._config.items():
                rule = self._rules.get(key)
                
                info[key] = {
                    'value': '***MASKED***' if rule and rule.sensitive else config_value.value,
                    'source': config_value.source.value,
                    'validated': config_value.validated,
                    'timestamp': config_value.timestamp.isoformat()
                }
                
                if rule:
                    info[key]['rule'] = {
                        'type': rule.validation_type.value,
                        'required': rule.required,
                        'description': rule.description
                    }
            
            return info
    
    def _set_value(self, key: str, value: Any, source: ConfigSource):
        """Internal method to set configuration value"""
        old_value = self._config.get(key)
        
        config_value = ConfigValue(
            key=key,
            value=value,
            source=source
        )
        
        self._config[key] = config_value
        
        # Notify watchers
        if old_value is None or old_value.value != value:
            for watcher in self._watchers:
                try:
                    watcher(key, value)
                except Exception as e:
                    logger.error(f"Watcher error for {key}: {e}")
    
    def _load_dict(self, data: Dict[str, Any], source: ConfigSource, prefix: str = ""):
        """Recursively load dictionary data"""
        for key, value in data.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if isinstance(value, dict):
                self._load_dict(value, source, f"{full_key}_")
            else:
                self._set_value(full_key, value, source)
    
    def _expand_variables(self, value: str) -> str:
        """Expand ${VAR} references in value"""
        pattern = r'\$\{([^}]+)\}'
        
        def replace(match):
            var_name = match.group(1)
            return self.get(var_name, os.environ.get(var_name, match.group(0)))
        
        return re.sub(pattern, replace, value)
    
    def _validate_value(self, value: Any, rule: ConfigRule):
        """Validate a value against a rule"""
        # Type validation
        if rule.validation_type == ValidationType.INTEGER:
            try:
                val = int(value)
                if rule.min_value is not None and val < rule.min_value:
                    raise ConfigValidationError(f"{rule.name}: value {val} < min {rule.min_value}")
                if rule.max_value is not None and val > rule.max_value:
                    raise ConfigValidationError(f"{rule.name}: value {val} > max {rule.max_value}")
            except ValueError:
                raise ConfigValidationError(f"{rule.name}: '{value}' is not a valid integer")
        
        elif rule.validation_type == ValidationType.FLOAT:
            try:
                val = float(value)
                if rule.min_value is not None and val < rule.min_value:
                    raise ConfigValidationError(f"{rule.name}: value {val} < min {rule.min_value}")
                if rule.max_value is not None and val > rule.max_value:
                    raise ConfigValidationError(f"{rule.name}: value {val} > max {rule.max_value}")
            except ValueError:
                raise ConfigValidationError(f"{rule.name}: '{value}' is not a valid float")
        
        elif rule.validation_type == ValidationType.BOOLEAN:
            if not isinstance(value, bool) and str(value).lower() not in ('true', 'false', 'yes', 'no', '1', '0'):
                raise ConfigValidationError(f"{rule.name}: '{value}' is not a valid boolean")
        
        elif rule.validation_type == ValidationType.EMAIL:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, str(value)):
                raise ConfigValidationError(f"{rule.name}: '{value}' is not a valid email")
        
        elif rule.validation_type == ValidationType.URL:
            url_pattern = r'^https?://[^\s]+$'
            if not re.match(url_pattern, str(value)):
                raise ConfigValidationError(f"{rule.name}: '{value}' is not a valid URL")
        
        elif rule.validation_type == ValidationType.PORT:
            try:
                port = int(value)
                if not (1 <= port <= 65535):
                    raise ConfigValidationError(f"{rule.name}: port {port} out of range (1-65535)")
            except ValueError:
                raise ConfigValidationError(f"{rule.name}: '{value}' is not a valid port")
        
        # Pattern validation
        if rule.pattern and not re.match(rule.pattern, str(value)):
            raise ConfigValidationError(f"{rule.name}: '{value}' does not match pattern {rule.pattern}")
        
        # Choices validation
        if rule.choices and value not in rule.choices:
            raise ConfigValidationError(f"{rule.name}: '{value}' not in allowed choices {rule.choices}")
