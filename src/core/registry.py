"""
Service and Component Registry System
Central registration and discovery for all system components.
"""

import logging
from typing import Any, Dict, List, Optional, Type, Callable
from dataclasses import dataclass, field
from datetime import datetime
import threading


logger = logging.getLogger(__name__)


@dataclass
class ServiceInfo:
    """Information about a registered service"""
    name: str
    service_type: Type
    instance: Any
    version: str = "1.0.0"
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: datetime = field(default_factory=datetime.now)
    health_check: Optional[Callable[[], bool]] = None


@dataclass
class ComponentInfo:
    """Information about a registered component"""
    name: str
    component_type: str
    factory: Callable
    dependencies: List[str] = field(default_factory=list)
    priority: int = 0
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class ServiceRegistry:
    """
    Central registry for services with health checking and discovery.
    """
    
    def __init__(self):
        self._services: Dict[str, ServiceInfo] = {}
        self._type_index: Dict[Type, List[str]] = {}
        self._capability_index: Dict[str, List[str]] = {}
        self._lock = threading.RLock()
        
        logger.info("ServiceRegistry initialized")
    
    def register(
        self,
        name: str,
        service: Any,
        service_type: Type,
        version: str = "1.0.0",
        description: str = "",
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        health_check: Optional[Callable[[], bool]] = None
    ) -> 'ServiceRegistry':
        """
        Register a service with the registry.
        
        Args:
            name: Unique service name
            service: Service instance
            service_type: Type/interface of the service
            version: Service version
            description: Human-readable description
            capabilities: List of service capabilities
            metadata: Additional metadata
            health_check: Optional health check function
        
        Returns:
            Self for method chaining
        """
        with self._lock:
            caps = capabilities or []
            
            info = ServiceInfo(
                name=name,
                service_type=service_type,
                instance=service,
                version=version,
                description=description,
                capabilities=caps,
                metadata=metadata or {},
                health_check=health_check
            )
            
            self._services[name] = info
            
            # Update type index
            if service_type not in self._type_index:
                self._type_index[service_type] = []
            self._type_index[service_type].append(name)
            
            # Update capability index
            for cap in caps:
                if cap not in self._capability_index:
                    self._capability_index[cap] = []
                self._capability_index[cap].append(name)
            
            logger.info(f"Registered service: {name} ({service_type.__name__})")
            
            return self
    
    def get(self, name: str) -> Optional[Any]:
        """Get a service by name"""
        with self._lock:
            info = self._services.get(name)
            return info.instance if info else None
    
    def get_by_type(self, service_type: Type) -> List[Any]:
        """Get all services implementing a specific type"""
        with self._lock:
            names = self._type_index.get(service_type, [])
            return [self._services[name].instance for name in names]
    
    def get_by_capability(self, capability: str) -> List[Any]:
        """Get all services with a specific capability"""
        with self._lock:
            names = self._capability_index.get(capability, [])
            return [self._services[name].instance for name in names]
    
    def get_info(self, name: str) -> Optional[ServiceInfo]:
        """Get service information"""
        with self._lock:
            return self._services.get(name)
    
    def list_services(self) -> List[str]:
        """List all registered service names"""
        with self._lock:
            return list(self._services.keys())
    
    def check_health(self, name: str) -> bool:
        """Check health of a specific service"""
        with self._lock:
            info = self._services.get(name)
            if not info or not info.health_check:
                return True  # No health check defined, assume healthy
            
            try:
                return info.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                return False
    
    def check_all_health(self) -> Dict[str, bool]:
        """Check health of all services"""
        with self._lock:
            results = {}
            for name in self._services.keys():
                results[name] = self.check_health(name)
            return results
    
    def unregister(self, name: str) -> bool:
        """Unregister a service"""
        with self._lock:
            if name not in self._services:
                return False
            
            info = self._services.pop(name)
            
            # Clean up indexes
            type_list = self._type_index.get(info.service_type, [])
            if name in type_list:
                type_list.remove(name)
            
            for cap in info.capabilities:
                cap_list = self._capability_index.get(cap, [])
                if name in cap_list:
                    cap_list.remove(name)
            
            logger.info(f"Unregistered service: {name}")
            return True


class ComponentRegistry:
    """
    Registry for pluggable components with priority and dependency management.
    """
    
    def __init__(self):
        self._components: Dict[str, ComponentInfo] = {}
        self._type_index: Dict[str, List[str]] = {}
        self._lock = threading.RLock()
        
        logger.info("ComponentRegistry initialized")
    
    def register(
        self,
        name: str,
        component_type: str,
        factory: Callable,
        dependencies: Optional[List[str]] = None,
        priority: int = 0,
        enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'ComponentRegistry':
        """
        Register a component.
        
        Args:
            name: Unique component name
            component_type: Type category (e.g., 'agent', 'tool', 'skill')
            factory: Factory function to create component
            dependencies: List of dependency names
            priority: Loading priority (higher = earlier)
            enabled: Whether component is enabled
            metadata: Additional metadata
        
        Returns:
            Self for method chaining
        """
        with self._lock:
            info = ComponentInfo(
                name=name,
                component_type=component_type,
                factory=factory,
                dependencies=dependencies or [],
                priority=priority,
                enabled=enabled,
                metadata=metadata or {}
            )
            
            self._components[name] = info
            
            # Update type index
            if component_type not in self._type_index:
                self._type_index[component_type] = []
            self._type_index[component_type].append(name)
            
            logger.info(f"Registered component: {name} (type={component_type})")
            
            return self
    
    def get(self, name: str) -> Optional[ComponentInfo]:
        """Get component info by name"""
        with self._lock:
            return self._components.get(name)
    
    def get_by_type(self, component_type: str, enabled_only: bool = True) -> List[ComponentInfo]:
        """Get all components of a specific type"""
        with self._lock:
            names = self._type_index.get(component_type, [])
            components = [self._components[name] for name in names]
            
            if enabled_only:
                components = [c for c in components if c.enabled]
            
            # Sort by priority (descending)
            components.sort(key=lambda c: c.priority, reverse=True)
            
            return components
    
    def create(self, name: str, **kwargs) -> Any:
        """Create component instance using its factory"""
        with self._lock:
            info = self._components.get(name)
            if not info:
                raise ValueError(f"Component '{name}' not found")
            
            if not info.enabled:
                raise ValueError(f"Component '{name}' is disabled")
            
            return info.factory(**kwargs)
    
    def enable(self, name: str) -> bool:
        """Enable a component"""
        with self._lock:
            info = self._components.get(name)
            if info:
                info.enabled = True
                logger.info(f"Enabled component: {name}")
                return True
            return False
    
    def disable(self, name: str) -> bool:
        """Disable a component"""
        with self._lock:
            info = self._components.get(name)
            if info:
                info.enabled = False
                logger.info(f"Disabled component: {name}")
                return True
            return False
    
    def list_types(self) -> List[str]:
        """List all component types"""
        with self._lock:
            return list(self._type_index.keys())
    
    def list_components(self, component_type: Optional[str] = None) -> List[str]:
        """List all component names, optionally filtered by type"""
        with self._lock:
            if component_type:
                return self._type_index.get(component_type, [])
            return list(self._components.keys())
    
    def get_dependency_order(self, component_type: Optional[str] = None) -> List[str]:
        """
        Get components in dependency resolution order using topological sort.
        
        Args:
            component_type: Optional type filter
        
        Returns:
            List of component names in dependency order
        """
        with self._lock:
            # Get components to sort
            if component_type:
                components = self.get_by_type(component_type)
                comp_names = [c.name for c in components]
            else:
                comp_names = list(self._components.keys())
            
            # Build dependency graph
            graph = {name: set(self._components[name].dependencies) for name in comp_names}
            
            # Topological sort using Kahn's algorithm
            in_degree = {name: 0 for name in comp_names}
            for deps in graph.values():
                for dep in deps:
                    if dep in in_degree:
                        in_degree[dep] += 1
            
            queue = [name for name in comp_names if in_degree[name] == 0]
            result = []
            
            while queue:
                node = queue.pop(0)
                result.append(node)
                
                for neighbor in graph.get(node, []):
                    if neighbor in in_degree:
                        in_degree[neighbor] -= 1
                        if in_degree[neighbor] == 0:
                            queue.append(neighbor)
            
            return result
