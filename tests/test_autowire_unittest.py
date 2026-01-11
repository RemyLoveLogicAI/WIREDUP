
import unittest
import threading
from src.core.autowire import AutoWire, Scope, CircularDependencyError, DependencyNotFoundError

class TestAutoWire(unittest.TestCase):
    """Tests for AutoWire dependency injection"""
    
    def test_singleton_registration(self):
        """Test singleton scope registration"""
        autowire = AutoWire()
        
        class Service:
            pass
        
        autowire.register('service', Service, Scope.SINGLETON)
        
        # Resolve twice
        instance1 = autowire.resolve('service')
        instance2 = autowire.resolve('service')
        
        # Should be same instance
        self.assertIs(instance1, instance2)
    
    def test_transient_registration(self):
        """Test transient scope registration"""
        autowire = AutoWire()
        
        class Service:
            pass
        
        autowire.register('service', Service, Scope.TRANSIENT)
        
        # Resolve twice
        instance1 = autowire.resolve('service')
        instance2 = autowire.resolve('service')
        
        # Should be different instances
        self.assertIsNot(instance1, instance2)
    
    def test_dependency_injection(self):
        """Test automatic dependency injection"""
        autowire = AutoWire()
        
        class Database:
            pass
        
        class Service:
            def __init__(self, database):
                self.database = database
        
        autowire.register('database', Database)
        autowire.register('service', Service)
        
        service = autowire.resolve('service')
        self.assertIsInstance(service.database, Database)
    
    def test_circular_dependency_detection(self):
        """Test circular dependency detection"""
        autowire = AutoWire()
        
        class ServiceA:
            def __init__(self, service_b):
                self.service_b = service_b
        
        class ServiceB:
            def __init__(self, service_a):
                self.service_a = service_a
        
        # Use lazy=True to allow registration before resolution
        autowire.register('service_a', ServiceA, lazy=True)
        autowire.register('service_b', ServiceB, lazy=True)
        
        with self.assertRaises(CircularDependencyError):
            autowire.resolve('service_a')
    
    def test_dependency_not_found(self):
        """Test missing dependency error"""
        autowire = AutoWire()
        
        with self.assertRaises(DependencyNotFoundError):
            autowire.resolve('nonexistent')

if __name__ == '__main__':
    unittest.main()
