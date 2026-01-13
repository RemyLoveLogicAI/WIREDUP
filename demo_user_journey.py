#!/usr/bin/env python
"""
User Journey Demo Runner
Demonstrates real-world usage scenarios from USER_JOURNEY.md
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.autowire import AutoWire, Scope
from src.config import EnvManager
from src.mcp import MCPProtocol, MCPRole, MCPMessageType
from src.agents.base_agent import BaseAgent, AgentContext


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DemoResearchAgent(BaseAgent):
    """Demo research agent"""
    
    async def execute(self, task: str, context: AgentContext):
        self.log_info(f"Researching: {task}")
        await asyncio.sleep(0.1)  # Simulate work
        
        return {
            'success': True,
            'agent': self.name,
            'findings': [
                f"Finding 1 for: {task}",
                f"Finding 2 for: {task}",
                f"Finding 3 for: {task}"
            ],
            'sources': ['source1', 'source2', 'source3']
        }


class DemoAnalysisAgent(BaseAgent):
    """Demo analysis agent"""
    
    async def execute(self, task: str, context: AgentContext):
        self.log_info(f"Analyzing: {task}")
        await asyncio.sleep(0.1)  # Simulate work
        
        # Access previous results from context
        findings = context.state.get('research_findings', [])
        
        return {
            'success': True,
            'agent': self.name,
            'patterns': ['Pattern A', 'Pattern B', 'Pattern C'],
            'insights': ['Insight 1', 'Insight 2'],
            'based_on': len(findings)
        }


class DemoCoordinator(BaseAgent):
    """Demo coordinator agent"""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.agents = []
    
    def add_agent(self, agent: BaseAgent):
        self.agents.append(agent)
    
    async def execute(self, task: str, context: AgentContext):
        self.log_info(f"Coordinating: {task}")
        
        results = []
        for agent in self.agents:
            result = await agent.execute(task, context)
            results.append(result)
            
            # Share data via context
            if agent.name == 'researcher':
                context.state['research_findings'] = result['findings']
        
        return {
            'success': True,
            'agent': self.name,
            'sub_results': results,
            'summary': f"Coordinated {len(results)} agents"
        }


async def demo_1_basic_agent():
    """Demo 1: Basic agent creation and execution"""
    print("\n" + "="*60)
    print("DEMO 1: Basic Agent Creation and Execution")
    print("="*60 + "\n")
    
    # Create and register agent
    autowire = AutoWire()
    autowire.register(
        name='demo_agent',
        factory=lambda: DemoResearchAgent('demo_agent', {'version': '1.0'}),
        scope=Scope.SINGLETON
    )
    
    # Resolve and execute
    agent = autowire.resolve('demo_agent')
    context = AgentContext(session_id='demo_001', user_id='demo_user')
    
    result = await agent.execute("AI market trends 2024", context)
    
    print(f"✅ Agent: {result['agent']}")
    print(f"✅ Success: {result['success']}")
    print(f"✅ Findings: {len(result['findings'])} items")
    for i, finding in enumerate(result['findings'], 1):
        print(f"   {i}. {finding}")
    print(f"✅ Sources: {', '.join(result['sources'])}")


async def demo_2_configuration():
    """Demo 2: Agent with configuration"""
    print("\n" + "="*60)
    print("DEMO 2: Agent with Configuration")
    print("="*60 + "\n")
    
    # Set up configuration
    env = EnvManager(auto_load=False)
    env.set('AGENT_MODEL', 'gpt-4')
    env.set('AGENT_TEMPERATURE', '0.7')
    env.set('AGENT_MAX_TOKENS', '4096')
    
    # Create agent with config
    agent_config = {
        'model': env.get('AGENT_MODEL'),
        'temperature': env.get_float('AGENT_TEMPERATURE'),
        'max_tokens': env.get_int('AGENT_MAX_TOKENS')
    }
    
    agent = DemoResearchAgent('configured_agent', agent_config)
    
    print(f"✅ Agent configured with:")
    print(f"   Model: {agent.get_config('model')}")
    print(f"   Temperature: {agent.get_config('temperature')}")
    print(f"   Max Tokens: {agent.get_config('max_tokens')}")
    
    context = AgentContext(session_id='demo_002')
    result = await agent.execute("Quantum computing advances", context)
    
    print(f"✅ Execution successful: {result['success']}")


async def demo_3_skills():
    """Demo 3: Agent with skills"""
    print("\n" + "="*60)
    print("DEMO 3: Agent with Skills")
    print("="*60 + "\n")
    
    # Define skills
    async def search_skill(query: str):
        return {'results': [f"Result for: {query}"], 'count': 1}
    
    async def summarize_skill(text: str):
        return {'summary': f"Summary: {text[:30]}..."}
    
    # Create agent and add skills
    agent = DemoResearchAgent('skilled_agent', {})
    agent.add_skill('search', search_skill)
    agent.add_skill('summarize', summarize_skill)
    
    print(f"✅ Skills available: search, summarize")
    print(f"✅ Has 'search' skill: {agent.has_skill('search')}")
    print(f"✅ Has 'summarize' skill: {agent.has_skill('summarize')}")
    
    # Use skills
    search_result = await agent.use_skill('search', query='AI trends')
    print(f"✅ Search result: {search_result}")
    
    summary_result = await agent.use_skill('summarize', text='This is a long text that needs summarization')
    print(f"✅ Summary result: {summary_result}")


async def demo_4_multi_agent():
    """Demo 4: Multi-agent coordination"""
    print("\n" + "="*60)
    print("DEMO 4: Multi-Agent Coordination")
    print("="*60 + "\n")
    
    # Create specialized agents
    research_agent = DemoResearchAgent('researcher', {'specialty': 'research'})
    analysis_agent = DemoAnalysisAgent('analyzer', {'specialty': 'analysis'})
    
    # Create coordinator
    coordinator = DemoCoordinator('coordinator')
    coordinator.add_agent(research_agent)
    coordinator.add_agent(analysis_agent)
    
    print(f"✅ Coordinator created with {len(coordinator.agents)} sub-agents")
    
    # Execute coordinated workflow
    context = AgentContext(
        session_id='demo_004',
        user_id='demo_user',
        state={}
    )
    
    result = await coordinator.execute("Analyze blockchain technology", context)
    
    print(f"✅ Coordination: {result['summary']}")
    print(f"✅ Results from {len(result['sub_results'])} agents:")
    for i, sub_result in enumerate(result['sub_results'], 1):
        print(f"   {i}. {sub_result['agent']}: {sub_result['success']}")
    
    print(f"✅ Shared context state keys: {list(context.state.keys())}")


async def demo_5_mcp_protocol():
    """Demo 5: MCP protocol integration"""
    print("\n" + "="*60)
    print("DEMO 5: MCP Protocol Integration")
    print("="*60 + "\n")
    
    # Initialize MCP
    mcp = MCPProtocol(session_id='demo_mcp')
    
    # Create MCP-enabled agent
    class MCPDemoAgent(BaseAgent):
        def __init__(self, name: str, mcp_protocol: MCPProtocol):
            super().__init__(name)
            self.mcp = mcp_protocol
        
        async def execute(self, task: str, context: AgentContext):
            # Send request
            request = self.mcp.send(
                content=task,
                role=MCPRole.USER,
                message_type=MCPMessageType.REQUEST
            )
            
            # Simulate processing
            result = f"Processed via MCP: {task}"
            
            # Send response
            response = self.mcp.send(
                content=result,
                role=MCPRole.ASSISTANT,
                message_type=MCPMessageType.RESPONSE
            )
            
            return {
                'success': True,
                'request_id': request.id,
                'response_id': response.id,
                'result': result
            }
    
    agent = MCPDemoAgent('mcp_agent', mcp)
    context = AgentContext(session_id='demo_005')
    
    result = await agent.execute("Test MCP communication", context)
    
    print(f"✅ MCP communication successful")
    print(f"✅ Request ID: {result['request_id']}")
    print(f"✅ Response ID: {result['response_id']}")
    
    # View history
    history = mcp.get_history()
    print(f"✅ MCP history: {len(history)} messages")
    for i, msg in enumerate(history, 1):
        print(f"   {i}. {msg.role.value}: {msg.content}")


async def demo_6_error_handling():
    """Demo 6: Error handling and recovery"""
    print("\n" + "="*60)
    print("DEMO 6: Error Handling and Recovery")
    print("="*60 + "\n")
    
    class ResilientDemoAgent(BaseAgent):
        def __init__(self, name: str):
            super().__init__(name)
            self.fallback_count = 0
        
        async def execute(self, task: str, context: AgentContext):
            try:
                if 'error' in task.lower():
                    raise ValueError("Simulated error in primary method")
                
                return {
                    'success': True,
                    'method': 'primary',
                    'result': f"Primary execution: {task}"
                }
            except ValueError as e:
                self.log_warning(f"Primary failed: {e}, using fallback")
                self.fallback_count += 1
                
                return {
                    'success': True,
                    'method': 'fallback',
                    'result': f"Fallback execution: {task}",
                    'fallback_count': self.fallback_count
                }
    
    agent = ResilientDemoAgent('resilient')
    context = AgentContext(session_id='demo_006')
    
    # Normal execution
    result1 = await agent.execute("normal task", context)
    print(f"✅ Normal task - Method: {result1['method']}")
    
    # Error scenario
    result2 = await agent.execute("trigger error task", context)
    print(f"✅ Error task - Method: {result2['method']}")
    print(f"✅ Fallback count: {result2['fallback_count']}")
    print(f"✅ Graceful recovery: {result2['success']}")


async def main():
    """Run all demos"""
    print("\n" + "🚀"*30)
    print("USER JOURNEY DEMO RUNNER")
    print("Demonstrating AI Auto-Wiring System Capabilities")
    print("🚀"*30)
    
    try:
        await demo_1_basic_agent()
        await demo_2_configuration()
        await demo_3_skills()
        await demo_4_multi_agent()
        await demo_5_mcp_protocol()
        await demo_6_error_handling()
        
        print("\n" + "="*60)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*60 + "\n")
        
        print("Next steps:")
        print("  1. Review USER_JOURNEY.md for detailed guides")
        print("  2. Check examples/ directory for more examples")
        print("  3. Run tests with: pytest tests/test_user_journey.py -v")
        print("  4. Start building your own agents!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
