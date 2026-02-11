"""
Comprehensive User Journey Tests
Tests real-world scenarios and end-to-end workflows for the AI Auto-Wiring System.
"""

import pytest
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List

from src.core.autowire import AutoWire, Scope, get_autowire
from src.config import EnvManager, ConfigLoader, get_config_loader
from src.mcp import MCPProtocol, MCPRole, MCPMessageType
from src.agents.base_agent import BaseAgent, AgentContext


# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """Agent for research tasks"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.research_results = []
    
    async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]:
        """Execute research task"""
        self.log_info(f"Starting research: {task}")
        
        # Simulate research
        await asyncio.sleep(0.1)
        
        result = {
            'success': True,
            'agent': self.name,
            'task': task,
            'findings': [
                f"Finding 1 for: {task}",
                f"Finding 2 for: {task}",
                f"Finding 3 for: {task}"
            ],
            'sources': ['source1', 'source2', 'source3']
        }
        
        self.research_results.append(result)
        self.log_info(f"Research completed: {task}")
        
        return result


class AnalysisAgent(BaseAgent):
    """Agent for data analysis"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.analysis_count = 0
    
    async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]:
        """Execute analysis task"""
        self.log_info(f"Starting analysis: {task}")
        
        # Simulate analysis
        await asyncio.sleep(0.1)
        self.analysis_count += 1
        
        result = {
            'success': True,
            'agent': self.name,
            'task': task,
            'analysis': {
                'patterns_found': 5,
                'confidence': 0.95,
                'insights': [
                    'Insight 1',
                    'Insight 2',
                    'Insight 3'
                ]
            },
            'analysis_number': self.analysis_count
        }
        
        self.log_info(f"Analysis completed: {task}")
        
        return result


class CoordinatorAgent(BaseAgent):
    """Agent that coordinates other agents"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.sub_agents: List[BaseAgent] = []
    
    def add_sub_agent(self, agent: BaseAgent):
        """Add a sub-agent"""
        self.sub_agents.append(agent)
        self.log_info(f"Added sub-agent: {agent.name}")
    
    async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]:
        """Execute coordinated task"""
        self.log_info(f"Coordinating task: {task}")
        
        # Execute on all sub-agents
        results = []
        for agent in self.sub_agents:
            result = await agent.execute(task, context)
            results.append(result)
        
        coordinated_result = {
            'success': True,
            'agent': self.name,
            'task': task,
            'sub_results': results,
            'summary': f"Coordinated {len(results)} sub-agents"
        }
        
        self.log_info(f"Coordination completed: {task}")
        
        return coordinated_result


class TestUserJourneyBasic:
    """Test basic user journeys"""
    
    @pytest.mark.asyncio
    async def test_journey_single_agent_workflow(self):
        """
        User Journey: Developer creates and uses a single agent
        
        Steps:
        1. Initialize auto-wiring system
        2. Create and register an agent
        3. Configure the agent
        4. Execute a task
        5. Verify results
        """
        # Step 1: Initialize auto-wiring
        autowire = AutoWire()
        
        # Step 2: Create and register agent
        autowire.register(
            name='research_agent',
            factory=lambda: ResearchAgent('research_agent', {'model': 'gpt-4'}),
            scope=Scope.SINGLETON
        )
        
        # Step 3: Resolve agent
        agent = autowire.resolve('research_agent')
        assert isinstance(agent, ResearchAgent)
        assert agent.name == 'research_agent'
        assert agent.get_config('model') == 'gpt-4'
        
        # Step 4: Create context and execute task
        context = AgentContext(
            session_id='test_session_1',
            user_id='user_123',
            metadata={'priority': 'high'}
        )
        
        result = await agent.execute("Research AI trends", context)
        
        # Step 5: Verify results
        assert result['success'] is True
        assert result['agent'] == 'research_agent'
        assert 'findings' in result
        assert len(result['findings']) == 3
        assert 'sources' in result
    
    @pytest.mark.asyncio
    async def test_journey_agent_with_skills(self):
        """
        User Journey: Agent with skills
        
        Steps:
        1. Create agent
        2. Add skills to agent
        3. Use skills during execution
        4. Verify skill usage
        """
        # Step 1: Create agent
        agent = AnalysisAgent('analysis_agent', {'version': '2.0'})
        
        # Step 2: Add skills
        async def pattern_detection_skill(data: str):
            return {'patterns': ['pattern1', 'pattern2'], 'count': 2}
        
        async def summarization_skill(data: str):
            return {'summary': f"Summary of {data}"}
        
        agent.add_skill('pattern_detection', pattern_detection_skill)
        agent.add_skill('summarization', summarization_skill)
        
        # Step 3: Verify skills
        assert agent.has_skill('pattern_detection')
        assert agent.has_skill('summarization')
        
        # Step 4: Use skills
        pattern_result = await agent.use_skill('pattern_detection', data='test data')
        assert pattern_result['count'] == 2
        assert len(pattern_result['patterns']) == 2
        
        summary_result = await agent.use_skill('summarization', data='test data')
        assert 'summary' in summary_result
    
    @pytest.mark.asyncio
    async def test_journey_configuration_management(self):
        """
        User Journey: Configuration management workflow
        
        Steps:
        1. Create environment manager
        2. Set configuration values
        3. Create agent with config
        4. Validate configuration usage
        """
        # Step 1: Create environment manager
        env_manager = EnvManager(auto_load=False)
        
        # Step 2: Set configuration values
        env_manager.set('AGENT_MODEL', 'gpt-4')
        env_manager.set('AGENT_TEMPERATURE', '0.7')
        env_manager.set('AGENT_MAX_TOKENS', '4096')
        env_manager.set('AGENT_TIMEOUT', '30')
        
        # Step 3: Create agent with config
        agent_config = {
            'model': env_manager.get('AGENT_MODEL'),
            'temperature': env_manager.get_float('AGENT_TEMPERATURE'),
            'max_tokens': env_manager.get_int('AGENT_MAX_TOKENS'),
            'timeout': env_manager.get_int('AGENT_TIMEOUT')
        }
        
        agent = ResearchAgent('configured_agent', agent_config)
        
        # Step 4: Validate configuration
        assert agent.get_config('model') == 'gpt-4'
        assert agent.get_config('temperature') == 0.7
        assert agent.get_config('max_tokens') == 4096
        assert agent.get_config('timeout') == 30


class TestUserJourneyMultiAgent:
    """Test multi-agent coordination journeys"""
    
    @pytest.mark.asyncio
    async def test_journey_multi_agent_coordination(self):
        """
        User Journey: Multi-agent coordination
        
        Steps:
        1. Create multiple specialized agents
        2. Create coordinator agent
        3. Register all agents
        4. Execute coordinated task
        5. Verify all agents worked together
        """
        # Step 1: Create specialized agents
        research_agent = ResearchAgent('research', {'specialty': 'web_search'})
        analysis_agent = AnalysisAgent('analysis', {'specialty': 'data_processing'})
        
        # Step 2: Create coordinator
        coordinator = CoordinatorAgent('coordinator', {'role': 'orchestrator'})
        coordinator.add_sub_agent(research_agent)
        coordinator.add_sub_agent(analysis_agent)
        
        # Step 3: Create context
        context = AgentContext(
            session_id='multi_agent_session',
            user_id='user_456',
            metadata={'workflow': 'research_and_analyze'}
        )
        
        # Step 4: Execute coordinated task
        result = await coordinator.execute("Analyze market trends", context)
        
        # Step 5: Verify coordination
        assert result['success'] is True
        assert result['agent'] == 'coordinator'
        assert 'sub_results' in result
        assert len(result['sub_results']) == 2
        
        # Verify both sub-agents executed
        agent_names = [r['agent'] for r in result['sub_results']]
        assert 'research' in agent_names
        assert 'analysis' in agent_names
    
    @pytest.mark.asyncio
    async def test_journey_agent_communication_via_context(self):
        """
        User Journey: Agents communicate via shared context
        
        Steps:
        1. Create first agent
        2. Execute and update context
        3. Create second agent
        4. Execute with updated context
        5. Verify data flow between agents
        """
        # Step 1: Create and execute first agent
        research_agent = ResearchAgent('researcher', {})
        
        context = AgentContext(
            session_id='shared_context_session',
            user_id='user_789',
            state={}
        )
        
        # Step 2: First agent execution
        research_result = await research_agent.execute("Research topic X", context)
        
        # Store result in context
        context.state['research_findings'] = research_result['findings']
        context.state['research_sources'] = research_result['sources']
        
        # Step 3: Second agent uses context data
        analysis_agent = AnalysisAgent('analyzer', {})
        
        # Step 4: Second agent execution with shared context
        analysis_result = await analysis_agent.execute("Analyze research findings", context)
        
        # Step 5: Verify data flow
        assert 'research_findings' in context.state
        assert 'research_sources' in context.state
        assert analysis_result['success'] is True
        assert len(context.state['research_findings']) == 3


class TestUserJourneyMCPIntegration:
    """Test MCP protocol integration journeys"""
    
    @pytest.mark.asyncio
    async def test_journey_mcp_agent_communication(self):
        """
        User Journey: Agent communication via MCP protocol
        
        Steps:
        1. Initialize MCP protocol
        2. Create agent with MCP
        3. Send messages via MCP
        4. Verify message flow
        """
        # Step 1: Initialize MCP
        mcp = MCPProtocol(session_id='mcp_test_session')
        
        # Step 2: Create agent
        class MCPAgent(BaseAgent):
            def __init__(self, name: str, mcp_protocol: MCPProtocol):
                super().__init__(name)
                self.mcp = mcp_protocol
            
            async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]:
                # Send request via MCP
                message = self.mcp.send(
                    content=task,
                    role=MCPRole.USER,
                    message_type=MCPMessageType.REQUEST
                )
                
                # Simulate processing
                await asyncio.sleep(0.1)
                
                # Send response
                response = self.mcp.send(
                    content=f"Processed: {task}",
                    role=MCPRole.ASSISTANT,
                    message_type=MCPMessageType.RESPONSE
                )
                
                return {
                    'success': True,
                    'request_id': message.id,
                    'response_id': response.id,
                    'result': response.content
                }
        
        agent = MCPAgent('mcp_agent', mcp)
        
        # Step 3: Execute with MCP
        context = AgentContext(session_id='mcp_session')
        result = await agent.execute("Test MCP communication", context)
        
        # Step 4: Verify MCP message flow
        assert result['success'] is True
        assert 'request_id' in result
        assert 'response_id' in result
        
        # Verify MCP history
        history = mcp.get_history()
        assert len(history) == 2
        assert history[0].role == MCPRole.USER
        assert history[1].role == MCPRole.ASSISTANT
    
    @pytest.mark.asyncio
    async def test_journey_mcp_context_export_import(self):
        """
        User Journey: MCP context persistence
        
        Steps:
        1. Create MCP session with messages
        2. Export context
        3. Create new MCP instance
        4. Import context
        5. Verify context restored
        """
        # Step 1: Create MCP with messages
        mcp1 = MCPProtocol(session_id='persistent_session')
        mcp1.send("Message 1", role=MCPRole.USER)
        mcp1.send("Response 1", role=MCPRole.ASSISTANT)
        mcp1.send("Message 2", role=MCPRole.USER)
        
        # Step 2: Export context
        context_data = mcp1.export_context()
        
        # Step 3: Create new MCP instance
        mcp2 = MCPProtocol()
        
        # Step 4: Import context
        mcp2.import_context(context_data)
        
        # Step 5: Verify restoration
        assert mcp2.session_id == 'persistent_session'
        history = mcp2.get_history()
        assert len(history) == 3
        assert history[0].content == "Message 1"
        assert history[1].content == "Response 1"
        assert history[2].content == "Message 2"


class TestUserJourneyErrorHandling:
    """Test error handling and recovery journeys"""
    
    @pytest.mark.asyncio
    async def test_journey_graceful_degradation(self):
        """
        User Journey: Graceful error handling
        
        Steps:
        1. Create agent with fallback logic
        2. Trigger error condition
        3. Verify fallback executes
        4. Verify graceful recovery
        """
        class ResilientAgent(BaseAgent):
            def __init__(self, name: str):
                super().__init__(name)
                self.primary_failed = False
                self.fallback_used = False
            
            async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]:
                try:
                    # Primary method
                    if 'force_error' in task:
                        raise ValueError("Simulated error")
                    
                    return {
                        'success': True,
                        'method': 'primary',
                        'result': f"Primary: {task}"
                    }
                except ValueError as e:
                    # Fallback method
                    self.primary_failed = True
                    self.fallback_used = True
                    self.log_warning(f"Primary failed, using fallback: {e}")
                    
                    return {
                        'success': True,
                        'method': 'fallback',
                        'result': f"Fallback: {task}",
                        'original_error': str(e)
                    }
        
        # Step 1: Create resilient agent
        agent = ResilientAgent('resilient')
        context = AgentContext(session_id='error_test')
        
        # Step 2: Normal execution
        normal_result = await agent.execute("normal task", context)
        assert normal_result['method'] == 'primary'
        assert agent.fallback_used is False
        
        # Step 3: Error condition
        error_result = await agent.execute("force_error task", context)
        
        # Step 4: Verify graceful recovery
        assert error_result['success'] is True
        assert error_result['method'] == 'fallback'
        assert agent.fallback_used is True
        assert 'original_error' in error_result
    
    @pytest.mark.asyncio
    async def test_journey_skill_not_available(self):
        """
        User Journey: Handle missing skill gracefully
        
        Steps:
        1. Create agent
        2. Attempt to use non-existent skill
        3. Verify appropriate error
        """
        agent = AnalysisAgent('analyzer', {})
        
        # Attempt to use non-existent skill
        with pytest.raises(ValueError) as exc_info:
            await agent.use_skill('nonexistent_skill', data='test')
        
        assert "not available" in str(exc_info.value)


class TestUserJourneyDependencyInjection:
    """Test dependency injection user journeys"""
    
    @pytest.mark.asyncio
    async def test_journey_autowire_dependency_chain(self):
        """
        User Journey: Complex dependency chain
        
        Steps:
        1. Create service dependency
        2. Create agent that depends on service
        3. Register both with autowire
        4. Resolve and verify injection
        """
        # Step 1: Create dependencies
        class DataService:
            def __init__(self):
                self.data_store = {}
            
            def store(self, key: str, value: Any):
                self.data_store[key] = value
            
            def retrieve(self, key: str):
                return self.data_store.get(key)
        
        class DataAgent(BaseAgent):
            def __init__(self, name: str, data_service: DataService):
                super().__init__(name)
                self.data_service = data_service
            
            async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]:
                # Use injected service
                self.data_service.store('last_task', task)
                stored_task = self.data_service.retrieve('last_task')
                
                return {
                    'success': True,
                    'task': task,
                    'stored_task': stored_task,
                    'service_available': self.data_service is not None
                }
        
        # Step 2: Register with autowire
        autowire = AutoWire()
        autowire.register('data_service', DataService, Scope.SINGLETON)
        
        # Register agent with factory that uses dependency injection
        def create_data_agent(data_service):
            return DataAgent('data_agent', data_service)
        
        autowire.register('data_agent', create_data_agent, Scope.SINGLETON)
        
        # Step 3: Resolve agent (service should be auto-injected)
        agent = autowire.resolve('data_agent')
        
        # Step 4: Verify injection
        assert isinstance(agent, DataAgent)
        assert agent.data_service is not None
        
        # Step 5: Test functionality
        context = AgentContext(session_id='di_test')
        result = await agent.execute("Test dependency injection", context)
        
        assert result['success'] is True
        assert result['service_available'] is True
        assert result['stored_task'] == "Test dependency injection"
    
    def test_journey_singleton_vs_transient(self):
        """
        User Journey: Understanding scopes
        
        Steps:
        1. Register singleton service
        2. Register transient service
        3. Resolve multiple times
        4. Verify scope behavior
        """
        autowire = AutoWire()
        
        class Counter:
            instance_count = 0
            
            def __init__(self):
                Counter.instance_count += 1
                self.id = Counter.instance_count
        
        # Reset counter
        Counter.instance_count = 0
        
        # Register singleton
        autowire.register('singleton_counter', Counter, Scope.SINGLETON)
        
        # Resolve multiple times
        s1 = autowire.resolve('singleton_counter')
        s2 = autowire.resolve('singleton_counter')
        
        # Verify singleton behavior
        assert s1 is s2
        assert s1.id == s2.id
        assert Counter.instance_count == 1
        
        # Register transient
        autowire.register('transient_counter', Counter, Scope.TRANSIENT)
        
        # Resolve multiple times
        t1 = autowire.resolve('transient_counter')
        t2 = autowire.resolve('transient_counter')
        
        # Verify transient behavior
        assert t1 is not t2
        assert t1.id != t2.id


class TestUserJourneyEndToEnd:
    """Complete end-to-end user journey tests"""
    
    @pytest.mark.asyncio
    async def test_journey_complete_workflow(self):
        """
        Complete User Journey: Full application workflow
        
        Scenario: User sets up system, creates agents, executes workflow
        
        Steps:
        1. Initialize system (autowire, config, mcp)
        2. Configure environment
        3. Create and register services
        4. Create and register agents
        5. Execute multi-step workflow
        6. Verify complete results
        """
        # Step 1: Initialize system
        autowire = AutoWire()
        env_manager = EnvManager(auto_load=False)
        mcp = MCPProtocol(session_id='complete_workflow')
        
        # Step 2: Configure environment
        env_manager.set('WORKFLOW_NAME', 'complete_test')
        env_manager.set('WORKFLOW_VERSION', '1.0')
        env_manager.set('MAX_AGENTS', '3')
        
        # Step 3: Register services
        autowire.register('mcp', lambda: mcp, Scope.SINGLETON)
        autowire.register('env', lambda: env_manager, Scope.SINGLETON)
        
        # Step 4: Create workflow agents
        research_agent = ResearchAgent(
            'researcher',
            {'source': env_manager.get('WORKFLOW_NAME')}
        )
        
        analysis_agent = AnalysisAgent(
            'analyzer',
            {'version': env_manager.get('WORKFLOW_VERSION')}
        )
        
        coordinator = CoordinatorAgent(
            'coordinator',
            {'max_agents': env_manager.get_int('MAX_AGENTS')}
        )
        
        coordinator.add_sub_agent(research_agent)
        coordinator.add_sub_agent(analysis_agent)
        
        # Step 5: Execute multi-step workflow
        context = AgentContext(
            session_id='complete_workflow_session',
            user_id='workflow_user',
            metadata={
                'workflow_name': env_manager.get('WORKFLOW_NAME'),
                'started_at': 'now'
            }
        )
        
        # Execute workflow
        final_result = await coordinator.execute(
            "Research and analyze AI trends",
            context
        )
        
        # Step 6: Verify complete workflow
        assert final_result['success'] is True
        assert final_result['agent'] == 'coordinator'
        assert len(final_result['sub_results']) == 2
        
        # Verify research agent result
        research_result = final_result['sub_results'][0]
        assert research_result['agent'] == 'researcher'
        assert 'findings' in research_result
        assert len(research_result['findings']) > 0
        
        # Verify analysis agent result
        analysis_result = final_result['sub_results'][1]
        assert analysis_result['agent'] == 'analyzer'
        assert 'analysis' in analysis_result
        assert analysis_result['analysis']['confidence'] > 0
        
        # Verify context was shared
        assert context.metadata['workflow_name'] == 'complete_test'
    
    @pytest.mark.asyncio
    async def test_journey_sequential_agent_pipeline(self):
        """
        User Journey: Sequential agent pipeline
        
        Scenario: Data flows through multiple agents in sequence
        
        Steps:
        1. Create pipeline of agents
        2. Pass data through pipeline
        3. Verify data transformation at each stage
        """
        # Step 1: Create pipeline agents
        agents = [
            ResearchAgent('stage1', {'stage': 1}),
            AnalysisAgent('stage2', {'stage': 2}),
            ResearchAgent('stage3', {'stage': 3})
        ]
        
        # Step 2: Execute pipeline
        context = AgentContext(
            session_id='pipeline_test',
            state={'pipeline_data': []}
        )
        
        task = "Process through pipeline"
        
        for i, agent in enumerate(agents):
            result = await agent.execute(task, context)
            
            # Add result to pipeline data
            context.state['pipeline_data'].append({
                'stage': i + 1,
                'agent': agent.name,
                'result': result
            })
        
        # Step 3: Verify pipeline execution
        pipeline_data = context.state['pipeline_data']
        assert len(pipeline_data) == 3
        
        # Verify each stage
        assert pipeline_data[0]['agent'] == 'stage1'
        assert pipeline_data[1]['agent'] == 'stage2'
        assert pipeline_data[2]['agent'] == 'stage3'
        
        # Verify all succeeded
        for stage_data in pipeline_data:
            assert stage_data['result']['success'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
