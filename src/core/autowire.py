"""
Auto-Wiring Core Engine
Revolutionary dependency injection system for AI agents and services.
"""

import inspect
import logging
from typing import Any, Dict, List, Optional, Type, Callable, get_type_hints
from dataclasses import dataclass, field
from enum import Enum
import threading
from functools import wraps


logger = logging.getLogger(__name__)


class Scope(Enum):
    """Dependency scope types"""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class DependencyMetadata:
    """Metadata for registered dependencies"""
    name: str
    factory: Callable
    scope: Scope = Scope.SINGLETON
    instance: Optional[Any] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    lazy: bool = False


class CircularDependencyError(Exception):
    """Raised when circular dependency is detected"""
    pass


class DependencyNotFoundError(Exception):
    """Raised when a required dependency cannot be resolved"""
    pass


class AutoWire:
    """
    Revolutionary Auto-Wiring Engine with intelligent dependency injection.
    
    Features:
    - Automatic dependency resolution
    - Circular dependency detection
    - Multiple scopes (Singleton, Transient, Scoped)
    - Lazy initialization
    - Type-based injection
    - Tag-based service location
    - Thread-safe operations
    """
    
    def __init__(self):
        self._registry: Dict[str, DependencyMetadata] = {}
        self._type_registry: Dict[Type, str] = {}
        self._resolving: set = set()
        self._lock = threading.RLock()
        self._scoped_instances: Dict[str, Any] = {}
        
        logger.info("AutoWire engine initialized")
    
    def register(
        self,
        name: str,
        factory: Callable,
        scope: Scope = Scope.SINGLETON,
        tags: Optional[List[str]] = None,
        lazy: bool = False,
        interface: Optional[Type] = None
    ) -> 'AutoWire':
        """
        Register a dependency with the auto-wiring system.
        
        Args:
            name: Unique identifier for the dependency
            factory: Factory function or class to create the dependency
            scope: Lifecycle scope (SINGLETON, TRANSIENT, SCOPED)
            tags: Optional tags for service location
            lazy: Whether to delay initialization until first use
            interface: Optional interface/type to register for type-based injection
        
        Returns:
            Self for method chaining
        """
        with self._lock:
            # Analyze dependencies from factory signature
            dependencies = self._analyze_dependencies(factory)
            
            metadata = DependencyMetadata(
                name=name,
                factory=factory,
                scope=scope,
                dependencies=dependencies,
                tags=tags or [],
                lazy=lazy
            )
            
            self._registry[name] = metadata
            
            # Register type mapping if interface provided
            if interface:
                self._type_registry[interface] = name
            
            logger.info(f"Registered dependency: {name} (scope={scope.value}, lazy={lazy})")
            
            # Initialize immediately if singleton and not lazy
            if scope == Scope.SINGLETON and not lazy:
                self._create_instance(metadata)
            
            return self
    
    def register_decorator(
        self,
        name: Optional[str] = None,
        scope: Scope = Scope.SINGLETON,
        tags: Optional[List[str]] = None,
        lazy: bool = False
    ):
        """
        Decorator for registering classes or functions.
        
        Usage:
            @autowire.register_decorator(name="my_service")
            class MyService:
                pass
        """
        def decorator(cls_or_func):
            dep_name = name or cls_or_func.__name__
            self.register(dep_name, cls_or_func, scope, tags, lazy)
            return cls_or_func
        return decorator
    
    def resolve(self, name: str) -> Any:
        """
        Resolve and return a dependency instance.
        
        Args:
            name: Name of the dependency to resolve
        
        Returns:
            Resolved dependency instance
        
        Raises:
            DependencyNotFoundError: If dependency is not registered
            CircularDependencyError: If circular dependency detected
        """
        with self._lock:
            if name not in self._registry:
                raise DependencyNotFoundError(f"Dependency '{name}' not found in registry")
            
            metadata = self._registry[name]
            
            # Check for circular dependencies
            if name in self._resolving:
                raise CircularDependencyError(
                    f"Circular dependency detected: {' -> '.join(self._resolving)} -> {name}"
                )
            
            # Return existing singleton instance
            if metadata.scope == Scope.SINGLETON and metadata.instance is not None:
                return metadata.instance
            
            # Return existing scoped instance
            if metadata.scope == Scope.SCOPED and name in self._scoped_instances:
                return self._scoped_instances[name]
            
            # Create new instance
            return self._create_instance(metadata)
    
    def resolve_by_type(self, interface: Type) -> Any:
        """
        Resolve dependency by its interface/type.
        
        Args:
            interface: Interface or type to resolve
        
        Returns:
            Resolved dependency instance
        """
        with self._lock:
            if interface not in self._type_registry:
                raise DependencyNotFoundError(
                    f"No dependency registered for type '{interface.__name__}'"
                )
            
            name = self._type_registry[interface]
            return self.resolve(name)
    
    def resolve_all(self, tag: str) -> List[Any]:
        """
        Resolve all dependencies with a specific tag.
        
        Args:
            tag: Tag to filter dependencies
        
        Returns:
            List of resolved dependency instances
        """
        with self._lock:
            instances = []
            for name, metadata in self._registry.items():
                if tag in metadata.tags:
                    instances.append(self.resolve(name))
            return instances
    
    def inject(self, func: Callable) -> Callable:
        """
        Decorator to automatically inject dependencies into function parameters.
        
        Usage:
            @autowire.inject
            def my_function(service: MyService):
                service.do_something()
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get type hints from function signature
            hints = get_type_hints(func)
            
            # Inject dependencies not provided in kwargs
            for param_name, param_type in hints.items():
                if param_name not in kwargs:
                    try:
                        kwargs[param_name] = self.resolve_by_type(param_type)
                    except DependencyNotFoundError:
                        # Try by name if type resolution fails
                        try:
                            kwargs[param_name] = self.resolve(param_name)
                        except DependencyNotFoundError:
                            pass  # Let function handle missing parameter
            
            return func(*args, **kwargs)
        
        return wrapper
    
    def create_scoped(self) -> 'ScopedContainer':
        """
        Create a new scoped container for scoped dependencies.
        
        Returns:
            ScopedContainer instance
        """
        return ScopedContainer(self)
    
    def _create_instance(self, metadata: DependencyMetadata) -> Any:
        """Create an instance with dependency injection"""
        self._resolving.add(metadata.name)
        
        try:
            # Resolve dependencies
            deps = {}
            for dep_name in metadata.dependencies:
                deps[dep_name] = self.resolve(dep_name)
            
            # Create instance
            if inspect.isclass(metadata.factory):
                instance = metadata.factory(**deps)
            else:
                instance = metadata.factory(**deps)
            
            # Store based on scope
            if metadata.scope == Scope.SINGLETON:
                metadata.instance = instance
            elif metadata.scope == Scope.SCOPED:
                self._scoped_instances[metadata.name] = instance
            
            logger.debug(f"Created instance of '{metadata.name}'")
            
            return instance
        
        finally:
            self._resolving.discard(metadata.name)
    
    def _analyze_dependencies(self, factory: Callable) -> List[str]:
        """Analyze factory signature to extract dependencies"""
        dependencies = []
        
        try:
            sig = inspect.signature(factory)
            for param_name, param in sig.parameters.items():
                if param_name != 'self' and param.default == inspect.Parameter.empty:
                    dependencies.append(param_name)
        except (ValueError, TypeError):
            pass  # Unable to inspect signature
        
        return dependencies
    
    def clear_scoped(self):
        """Clear all scoped instances"""
        with self._lock:
            self._scoped_instances.clear()
            logger.debug("Cleared scoped instances")
    
    def get_registry_info(self) -> Dict[str, Dict]:
        """Get information about all registered dependencies"""
        with self._lock:
            info = {}
            for name, metadata in self._registry.items():
                info[name] = {
                    'scope': metadata.scope.value,
                    'dependencies': metadata.dependencies,
                    'tags': metadata.tags,
                    'lazy': metadata.lazy,
                    'initialized': metadata.instance is not None
                }
            return info


class ScopedContainer:
    """Container for managing scoped dependencies"""
    
    def __init__(self, autowire: AutoWire):
        self._autowire = autowire
        self._instances: Dict[str, Any] = {}
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._instances.clear()
    
    def resolve(self, name: str) -> Any:
        """Resolve dependency within this scope"""
        if name in self._instances:
            return self._instances[name]
        
        instance = self._autowire.resolve(name)
        self._instances[name] = instance
        return instance


# Global auto-wire instance
_global_autowire: Optional[AutoWire] = None


def get_autowire() -> AutoWire:
    """Get or create global AutoWire instance"""
    global _global_autowire
    if _global_autowire is None:
        _global_autowire = AutoWire()
    return _global_autowire


def inject(func: Callable) -> Callable:
    """Global inject decorator using default autowire instance"""
    return get_autowire().inject(func)
