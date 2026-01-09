"""
Test Suite for AI Auto-Wiring System
"""

import pytest
import asyncio
from src.core.autowire import AutoWire, Scope, CircularDependencyError, DependencyNotFoundError
from src.config import EnvManager, ConfigRule, ValidationType
from src.mcp import MCPProtocol, MCPRole, MCPMessageType
from src.agents.base_agent import BaseAgent, AgentContext


class TestAutoWire:
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
        assert instance1 is instance2
    
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
        assert instance1 is not instance2
    
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
        assert isinstance(service.database, Database)
    
    def test_circular_dependency_detection(self):
        """Test circular dependency detection"""
        autowire = AutoWire()
        
        class ServiceA:
            def __init__(self, service_b):
                self.service_b = service_b
        
        class ServiceB:
            def __init__(self, service_a):
                self.service_a = service_a
        
        autowire.register('service_a', ServiceA)
        autowire.register('service_b', ServiceB)
        
        with pytest.raises(CircularDependencyError):
            autowire.resolve('service_a')
    
    def test_dependency_not_found(self):
        """Test missing dependency error"""
        autowire = AutoWire()
        
        with pytest.raises(DependencyNotFoundError):
            autowire.resolve('nonexistent')


class TestEnvManager:
    """Tests for Environment Configuration Manager"""
    
    def test_config_loading(self, tmp_path):
        """Test configuration loading"""
        env_manager = EnvManager(config_dir=tmp_path, auto_load=False)
        
        env_manager.set('TEST_KEY', 'test_value')
        assert env_manager.get('TEST_KEY') == 'test_value'
    
    def test_type_conversion(self):
        """Test type conversion helpers"""
        env_manager = EnvManager(auto_load=False)
        
        env_manager.set('INT_VALUE', '42')
        env_manager.set('BOOL_VALUE', 'true')
        env_manager.set('LIST_VALUE', 'a,b,c')
        
        assert env_manager.get_int('INT_VALUE') == 42
        assert env_manager.get_bool('BOOL_VALUE') is True
        assert env_manager.get_list('LIST_VALUE') == ['a', 'b', 'c']
    
    def test_validation_rules(self):
        """Test configuration validation"""
        env_manager = EnvManager(auto_load=False)
        
        rule = ConfigRule(
            name='PORT',
            validation_type=ValidationType.PORT,
            required=True,
            min_value=1,
            max_value=65535
        )
        
        env_manager.add_rule(rule)
        env_manager.set('PORT', '8080')
        
        assert env_manager.validate()


class TestMCPProtocol:
    """Tests for Model Context Protocol"""
    
    def test_message_creation(self):
        """Test MCP message creation"""
        mcp = MCPProtocol()
        
        message = mcp.send(
            content="Test message",
            role=MCPRole.USER,
            message_type=MCPMessageType.REQUEST
        )
        
        assert message.content == "Test message"
        assert message.role == MCPRole.USER
        assert message.type == MCPMessageType.REQUEST
    
    def test_context_management(self):
        """Test context management"""
        mcp = MCPProtocol()
        
        mcp.send("Message 1", role=MCPRole.USER)
        mcp.send("Message 2", role=MCPRole.ASSISTANT)
        
        history = mcp.get_history()
        assert len(history) == 2
    
    def test_context_export_import(self):
        """Test context export and import"""
        mcp1 = MCPProtocol(session_id="test_session")
        mcp1.send("Test message", role=MCPRole.USER)
        
        # Export
        context_data = mcp1.export_context()
        
        # Import to new instance
        mcp2 = MCPProtocol()
        mcp2.import_context(context_data)
        
        assert mcp2.session_id == "test_session"
        assert len(mcp2.get_history()) == 1


class TestBaseAgent:
    """Tests for Base Agent"""
    
    @pytest.mark.asyncio
    async def test_agent_creation(self):
        """Test agent creation"""
        
        class TestAgent(BaseAgent):
            async def execute(self, task: str, context: AgentContext):
                return {'result': f"Executed: {task}"}
        
        agent = TestAgent('test_agent', {'version': '1.0'})
        assert agent.name == 'test_agent'
        assert agent.get_config('version') == '1.0'
    
    @pytest.mark.asyncio
    async def test_skill_management(self):
        """Test skill management"""
        
        class TestAgent(BaseAgent):
            async def execute(self, task: str, context: AgentContext):
                if self.has_skill('test_skill'):
                    return await self.use_skill('test_skill', task=task)
                return {'result': 'No skill'}
        
        async def test_skill(task: str):
            return {'result': f"Skill executed: {task}"}
        
        agent = TestAgent('test_agent')
        agent.add_skill('test_skill', test_skill)
        
        assert agent.has_skill('test_skill')
        
        context = AgentContext(session_id='test_123')
        result = await agent.execute('test task', context)
        
        assert 'result' in result


class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_stack_integration(self):
        """Test full stack integration"""
        
        # Setup autowire
        autowire = AutoWire()
        
        # Create agent
        class IntegrationAgent(BaseAgent):
            def __init__(self, name: str, mcp: MCPProtocol):
                super().__init__(name)
                self.mcp = mcp
            
            async def execute(self, task: str, context: AgentContext):
                # Send via MCP
                message = self.mcp.send(
                    content=task,
                    role=MCPRole.USER
                )
                
                return {
                    'message_id': message.id,
                    'result': f"Processed: {task}"
                }
        
        # Register components
        autowire.register('mcp', lambda: MCPProtocol(), Scope.SINGLETON)
        autowire.register(
            'agent',
            lambda mcp: IntegrationAgent('integration_agent', mcp),
            Scope.SINGLETON
        )
        
        # Resolve and test
        agent = autowire.resolve('agent')
        context = AgentContext(session_id='test_456')
        result = await agent.execute('test task', context)
        
        assert 'message_id' in result
        assert result['result'] == "Processed: test task"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
