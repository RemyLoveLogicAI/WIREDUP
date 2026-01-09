"""
Configuration Auto-Discovery and Loading System
Intelligent configuration loading from multiple sources with merging.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import os


logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Advanced configuration loader with auto-discovery and hierarchical merging.
    
    Load order (later sources override earlier):
    1. Default config files (config/default.json)
    2. Environment-specific configs (config/{env}.json)
    3. Local overrides (config/local.json)
    4. .env files
    5. Environment variables
    6. Command-line arguments
    """
    
    def __init__(
        self,
        base_dir: Optional[Path] = None,
        env: str = "development",
        config_dirs: Optional[List[str]] = None
    ):
        self.base_dir = base_dir or Path.cwd()
        self.env = env
        self.config_dirs = config_dirs or ['config', 'configs', '.config']
        self._merged_config: Dict[str, Any] = {}
        
        logger.info(f"ConfigLoader initialized (env={env}, base={self.base_dir})")
    
    def discover_and_load(self) -> Dict[str, Any]:
        """
        Discover and load all configuration sources.
        
        Returns:
            Merged configuration dictionary
        """
        # 1. Find configuration directory
        config_dir = self._find_config_dir()
        
        if config_dir:
            logger.info(f"Found config directory: {config_dir}")
            
            # 2. Load default config
            self._load_config_file(config_dir / "default.json", merge=True)
            self._load_config_file(config_dir / "default.yaml", merge=True)
            
            # 3. Load environment-specific config
            self._load_config_file(config_dir / f"{self.env}.json", merge=True)
            self._load_config_file(config_dir / f"{self.env}.yaml", merge=True)
            
            # 4. Load local overrides
            self._load_config_file(config_dir / "local.json", merge=True)
            self._load_config_file(config_dir / "local.yaml", merge=True)
        
        # 5. Load .env files
        self._load_env_file()
        
        # 6. Load environment variables with AI_ prefix
        self._load_env_variables()
        
        logger.info(f"Loaded {len(self._merged_config)} configuration keys")
        
        return self._merged_config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'mcp.port')"""
        keys = key.split('.')
        value = self._merged_config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration"""
        return self._merged_config.copy()
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self._merged_config
        
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def merge(self, config: Dict[str, Any]):
        """Merge configuration dictionary"""
        self._deep_merge(self._merged_config, config)
    
    def _find_config_dir(self) -> Optional[Path]:
        """Find configuration directory"""
        for dir_name in self.config_dirs:
            config_dir = self.base_dir / dir_name
            if config_dir.exists() and config_dir.is_dir():
                return config_dir
        
        return None
    
    def _load_config_file(self, file_path: Path, merge: bool = True):
        """Load configuration from JSON or YAML file"""
        if not file_path.exists():
            return
        
        try:
            if file_path.suffix == '.json':
                with open(file_path, 'r') as f:
                    config = json.load(f)
                    logger.info(f"Loaded config file: {file_path}")
                    
                    if merge:
                        self._deep_merge(self._merged_config, config)
                    else:
                        self._merged_config = config
            
            elif file_path.suffix in ('.yaml', '.yml'):
                try:
                    import yaml
                    with open(file_path, 'r') as f:
                        config = yaml.safe_load(f)
                        logger.info(f"Loaded config file: {file_path}")
                        
                        if merge:
                            self._deep_merge(self._merged_config, config)
                        else:
                            self._merged_config = config
                
                except ImportError:
                    logger.warning("PyYAML not installed, skipping YAML files")
        
        except Exception as e:
            logger.error(f"Failed to load config file {file_path}: {e}")
    
    def _load_env_file(self):
        """Load .env file"""
        env_files = [
            self.base_dir / f".env.{self.env}",
            self.base_dir / ".env.local",
            self.base_dir / ".env"
        ]
        
        for env_file in env_files:
            if env_file.exists():
                logger.info(f"Loading .env file: {env_file}")
                
                try:
                    with open(env_file, 'r') as f:
                        for line in f:
                            line = line.strip()
                            
                            if not line or line.startswith('#'):
                                continue
                            
                            if '=' in line:
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip().strip('"').strip("'")
                                
                                # Convert key to nested structure
                                self._set_from_env_key(key, value)
                
                except Exception as e:
                    logger.error(f"Failed to load .env file {env_file}: {e}")
                
                break  # Only load first found .env file
    
    def _load_env_variables(self):
        """Load environment variables with AI_ prefix"""
        for key, value in os.environ.items():
            if key.startswith('AI_'):
                # Remove AI_ prefix and convert to nested structure
                config_key = key[3:]  # Remove 'AI_'
                self._set_from_env_key(config_key, value)
                logger.debug(f"Loaded env var: {key}")
    
    def _set_from_env_key(self, key: str, value: str):
        """Convert environment variable key to nested config structure"""
        # Convert KEY_SUBKEY to key.subkey
        parts = key.lower().split('_')
        
        config = self._merged_config
        for part in parts[:-1]:
            if part not in config:
                config[part] = {}
            config = config[part]
        
        # Try to parse value as JSON for lists/dicts
        try:
            parsed_value = json.loads(value)
            config[parts[-1]] = parsed_value
        except (json.JSONDecodeError, ValueError):
            # Try to convert to boolean
            if value.lower() in ('true', 'false'):
                config[parts[-1]] = value.lower() == 'true'
            # Try to convert to number
            elif value.isdigit():
                config[parts[-1]] = int(value)
            elif self._is_float(value):
                config[parts[-1]] = float(value)
            else:
                config[parts[-1]] = value
    
    def _deep_merge(self, base: Dict, update: Dict):
        """Deep merge two dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _is_float(self, value: str) -> bool:
        """Check if string can be converted to float"""
        try:
            float(value)
            return True
        except ValueError:
            return False


# Create default global config loader
_global_loader: Optional[ConfigLoader] = None


def get_config_loader(
    base_dir: Optional[Path] = None,
    env: Optional[str] = None
) -> ConfigLoader:
    """Get or create global config loader"""
    global _global_loader
    
    if _global_loader is None:
        _global_loader = ConfigLoader(
            base_dir=base_dir,
            env=env or os.getenv('AI_ENV', 'development')
        )
        _global_loader.discover_and_load()
    
    return _global_loader


def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value using global loader"""
    return get_config_loader().get(key, default)
