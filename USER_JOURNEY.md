# 🚀 User Journey Guide - AI Auto-Wiring System

> Comprehensive guide to real-world usage scenarios and workflows

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started Journey](#getting-started-journey)
3. [Basic Workflows](#basic-workflows)
4. [Advanced Scenarios](#advanced-scenarios)
5. [Multi-Agent Coordination](#multi-agent-coordination)
6. [Error Handling & Recovery](#error-handling--recovery)
7. [Production Deployment](#production-deployment)
8. [Best Practices](#best-practices)

---

## Introduction

This guide walks through real user journeys and common workflows when using the AI Auto-Wiring System. Each scenario includes step-by-step instructions with code examples.

### Who This Guide Is For

- **Developers** building AI agent applications
- **System Architects** designing multi-agent systems
- **DevOps Engineers** deploying AI solutions
- **Researchers** experimenting with agent frameworks

---

## Getting Started Journey

### Journey 1: "Hello World" - Your First Agent

**Scenario**: Create a simple agent that executes a task.

**Duration**: 5 minutes

**Steps**:

```python
# Step 1: Import required modules
from src.core.autowire import AutoWire, Scope
from src.agents.base_agent import BaseAgent, AgentContext

# Step 2: Define your agent
class MyFirstAgent(BaseAgent):
    async def execute(self, task: str, context: AgentContext):
        self.log_info(f"Executing: {task}")
        return {
            'success': True,
            'result': f"Completed: {task}"
        }

# Step 3: Initialize the auto-wiring system
autowire = AutoWire()

# Step 4: Register your agent
autowire.register(
    name='my_agent',
    factory=lambda: MyFirstAgent('my_agent'),
    scope=Scope.SINGLETON
)

# Step 5: Resolve and use your agent
agent = autowire.resolve('my_agent')

# Step 6: Execute a task
context = AgentContext(session_id='demo_001')
result = await agent.execute("Say hello!", context)

print(result)
# Output: {'success': True, 'result': 'Completed: Say hello!'}
```

**What You Learned**:
- ✅ Creating a basic agent
- ✅ Using the auto-wiring system
- ✅ Executing agent tasks
- ✅ Working with contexts

---

## Basic Workflows

### Journey 2: Agent with Configuration

**Scenario**: Configure an agent with environment-specific settings.

**Duration**: 10 minutes

```python
from src.config import EnvManager

# Step 1: Set up environment configuration
env = EnvManager(auto_load=False)
env.set('AGENT_MODEL', 'gpt-4')
env.set('AGENT_TEMPERATURE', '0.7')
env.set('AGENT_MAX_TOKENS', '4096')

# Step 2: Create agent with configuration
agent_config = {
    'model': env.get('AGENT_MODEL'),
    'temperature': env.get_float('AGENT_TEMPERATURE'),
    'max_tokens': env.get_int('AGENT_MAX_TOKENS')
}

class ConfiguredAgent(BaseAgent):
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self.model = config.get('model')
    
    async def execute(self, task: str, context: AgentContext):
        return {
            'success': True,
            'model': self.model,
            'task': task
        }

# Step 3: Use configured agent
agent = ConfiguredAgent('configured_agent', agent_config)
context = AgentContext(session_id='config_demo')
result = await agent.execute("Test with config", context)

print(f"Used model: {result['model']}")  # Output: Used model: gpt-4
```

**What You Learned**:
- ✅ Environment configuration management
- ✅ Type conversion (string to int/float)
- ✅ Passing configuration to agents

---

### Journey 3: Agent with Skills

**Scenario**: Add capabilities to agents using the skills system.

**Duration**: 15 minutes

```python
# Step 1: Define skills
async def search_skill(query: str):
    """Simulate web search"""
    return {
        'results': [f"Result for: {query}"],
        'count': 1
    }

async def summarize_skill(text: str):
    """Simulate summarization"""
    return {
        'summary': f"Summary: {text[:50]}..."
    }

# Step 2: Create agent and add skills
class SkillfulAgent(BaseAgent):
    async def execute(self, task: str, context: AgentContext):
        # Use skills if available
        if self.has_skill('search'):
            search_results = await self.use_skill('search', query=task)
            
            if self.has_skill('summarize'):
                summary = await self.use_skill(
                    'summarize',
                    text=str(search_results)
                )
                
                return {
                    'success': True,
                    'search_results': search_results,
                    'summary': summary
                }
        
        return {'success': False, 'error': 'Skills not available'}

# Step 3: Register skills
agent = SkillfulAgent('skilled_agent')
agent.add_skill('search', search_skill)
agent.add_skill('summarize', summarize_skill)

# Step 4: Execute with skills
context = AgentContext(session_id='skills_demo')
result = await agent.execute("AI trends", context)

print(result['summary'])
```

**What You Learned**:
- ✅ Creating reusable skills
- ✅ Adding skills to agents
- ✅ Using skills in agent execution
- ✅ Composing skills for complex tasks

---

## Advanced Scenarios

### Journey 4: Dependency Injection

**Scenario**: Use automatic dependency injection for complex agent architectures.

**Duration**: 20 minutes

```python
from src.core.autowire import AutoWire, Scope

# Step 1: Define service dependencies
class DatabaseService:
    def __init__(self):
        self.data = {}
    
    def save(self, key: str, value: any):
        self.data[key] = value
    
    def load(self, key: str):
        return self.data.get(key)

class LoggingService:
    def __init__(self):
        self.logs = []
    
    def log(self, message: str):
        self.logs.append(message)

# Step 2: Define agent with dependencies
class ServiceAgent(BaseAgent):
    def __init__(self, name: str, db: DatabaseService, logger: LoggingService):
        super().__init__(name)
        self.db = db
        self.logger = logger
    
    async def execute(self, task: str, context: AgentContext):
        self.logger.log(f"Executing: {task}")
        self.db.save('last_task', task)
        
        return {
            'success': True,
            'task': task,
            'logs_count': len(self.logger.logs)
        }

# Step 3: Register dependencies with autowire
autowire = AutoWire()
autowire.register('db', DatabaseService, Scope.SINGLETON)
autowire.register('logger', LoggingService, Scope.SINGLETON)

# Step 4: Register agent with dependency injection
def create_service_agent(db, logger):
    return ServiceAgent('service_agent', db, logger)

autowire.register('service_agent', create_service_agent, Scope.SINGLETON)

# Step 5: Resolve (dependencies auto-injected)
agent = autowire.resolve('service_agent')

# Step 6: Use agent
context = AgentContext(session_id='di_demo')
result = await agent.execute("Process data", context)
```

**What You Learned**:
- ✅ Defining service dependencies
- ✅ Automatic dependency injection
- ✅ Singleton vs Transient scopes
- ✅ Complex object graphs

---

## Multi-Agent Coordination

### Journey 5: Multi-Agent Workflow

**Scenario**: Coordinate multiple agents to complete a complex task.

**Duration**: 25 minutes

```python
# Step 1: Define specialized agents
class ResearchAgent(BaseAgent):
    async def execute(self, task: str, context: AgentContext):
        self.log_info(f"Researching: {task}")
        return {
            'agent': 'research',
            'findings': ['Finding 1', 'Finding 2', 'Finding 3'],
            'sources': ['source1', 'source2']
        }

class AnalysisAgent(BaseAgent):
    async def execute(self, task: str, context: AgentContext):
        self.log_info(f"Analyzing: {task}")
        
        # Access previous results from context
        findings = context.state.get('research_findings', [])
        
        return {
            'agent': 'analysis',
            'patterns': ['Pattern A', 'Pattern B'],
            'based_on_findings': len(findings)
        }

class ReportAgent(BaseAgent):
    async def execute(self, task: str, context: AgentContext):
        self.log_info(f"Generating report: {task}")
        
        return {
            'agent': 'report',
            'report': 'Final comprehensive report',
            'sections': ['intro', 'findings', 'analysis', 'conclusion']
        }

# Step 2: Create coordinator
class WorkflowCoordinator(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name)
        self.agents = {}
    
    def add_agent(self, role: str, agent: BaseAgent):
        self.agents[role] = agent
    
    async def execute(self, task: str, context: AgentContext):
        results = {}
        
        # Step 1: Research
        if 'research' in self.agents:
            research_result = await self.agents['research'].execute(task, context)
            results['research'] = research_result
            context.state['research_findings'] = research_result['findings']
        
        # Step 2: Analysis
        if 'analysis' in self.agents:
            analysis_result = await self.agents['analysis'].execute(task, context)
            results['analysis'] = analysis_result
            context.state['analysis_patterns'] = analysis_result['patterns']
        
        # Step 3: Report
        if 'report' in self.agents:
            report_result = await self.agents['report'].execute(task, context)
            results['report'] = report_result
        
        return {
            'success': True,
            'workflow': 'complete',
            'results': results
        }

# Step 3: Set up workflow
coordinator = WorkflowCoordinator('coordinator')
coordinator.add_agent('research', ResearchAgent('researcher'))
coordinator.add_agent('analysis', AnalysisAgent('analyzer'))
coordinator.add_agent('report', ReportAgent('reporter'))

# Step 4: Execute workflow
context = AgentContext(session_id='workflow_demo', state={})
final_result = await coordinator.execute("Analyze AI market trends", context)

print(f"Workflow complete: {final_result['workflow']}")
print(f"Stages completed: {list(final_result['results'].keys())}")
```

**What You Learned**:
- ✅ Creating specialized agents
- ✅ Coordinating multiple agents
- ✅ Sharing state between agents
- ✅ Sequential workflow execution

---

### Journey 6: MCP Protocol Integration

**Scenario**: Use Model Context Protocol for standardized agent communication.

**Duration**: 20 minutes

```python
from src.mcp import MCPProtocol, MCPRole, MCPMessageType

# Step 1: Initialize MCP
mcp = MCPProtocol(session_id='mcp_demo')

# Step 2: Create MCP-enabled agent
class MCPAgent(BaseAgent):
    def __init__(self, name: str, mcp_protocol: MCPProtocol):
        super().__init__(name)
        self.mcp = mcp_protocol
    
    async def execute(self, task: str, context: AgentContext):
        # Send user message
        request = self.mcp.send(
            content=task,
            role=MCPRole.USER,
            message_type=MCPMessageType.REQUEST
        )
        
        # Process (simulate AI processing)
        result = f"Processed: {task}"
        
        # Send assistant response
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

# Step 3: Use MCP agent
agent = MCPAgent('mcp_agent', mcp)
context = AgentContext(session_id='mcp_demo')
result = await agent.execute("Hello MCP!", context)

# Step 4: View MCP history
history = mcp.get_history()
print(f"MCP messages: {len(history)}")
for msg in history:
    print(f"{msg.role}: {msg.content}")

# Step 5: Export context for persistence
context_data = mcp.export_context()
print(f"Context exported with {len(context_data['messages'])} messages")
```

**What You Learned**:
- ✅ MCP protocol initialization
- ✅ Sending and receiving MCP messages
- ✅ Managing conversation history
- ✅ Context persistence and export

---

## Error Handling & Recovery

### Journey 7: Graceful Error Handling

**Scenario**: Build resilient agents with fallback mechanisms.

**Duration**: 15 minutes

```python
# Step 1: Define resilient agent
class ResilientAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name)
        self.fallback_count = 0
    
    async def execute(self, task: str, context: AgentContext):
        try:
            # Primary method
            return await self._primary_execution(task, context)
        except ValueError as e:
            # Fallback method
            self.log_warning(f"Primary method failed: {e}")
            return await self._fallback_execution(task, context)
        except Exception as e:
            # Last resort error handling
            self.log_error(f"All methods failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_used': True
            }
    
    async def _primary_execution(self, task: str, context: AgentContext):
        # Check if we should simulate failure
        if 'error' in task.lower():
            raise ValueError("Simulated primary method error")
        
        return {
            'success': True,
            'method': 'primary',
            'result': f"Primary: {task}"
        }
    
    async def _fallback_execution(self, task: str, context: AgentContext):
        self.fallback_count += 1
        return {
            'success': True,
            'method': 'fallback',
            'result': f"Fallback: {task}",
            'fallback_count': self.fallback_count
        }

# Step 2: Test resilience
agent = ResilientAgent('resilient')
context = AgentContext(session_id='error_demo')

# Normal execution
result1 = await agent.execute("normal task", context)
print(f"Method used: {result1['method']}")  # Output: primary

# Error scenario
result2 = await agent.execute("trigger error", context)
print(f"Method used: {result2['method']}")  # Output: fallback
print(f"Fallback count: {result2['fallback_count']}")  # Output: 1
```

**What You Learned**:
- ✅ Try-catch error handling
- ✅ Fallback mechanisms
- ✅ Graceful degradation
- ✅ Error logging and monitoring

---

## Production Deployment

### Journey 8: Complete Production Setup

**Scenario**: Deploy a production-ready multi-agent system.

**Duration**: 30 minutes

```python
import logging
from pathlib import Path

# Step 1: Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_system.log'),
        logging.StreamHandler()
    ]
)

# Step 2: Load production configuration
from src.config import EnvManager, ConfigRule, ValidationType

env = EnvManager()
env.add_rule(ConfigRule(
    name='AGENT_API_KEY',
    validation_type=ValidationType.REQUIRED,
    required=True
))
env.add_rule(ConfigRule(
    name='AGENT_PORT',
    validation_type=ValidationType.PORT,
    required=True,
    min_value=1024,
    max_value=65535
))

# Validate configuration
if not env.validate():
    raise ValueError("Configuration validation failed")

# Step 3: Set up production autowire
autowire = AutoWire()

# Register services
autowire.register('env', lambda: env, Scope.SINGLETON)
autowire.register('mcp', lambda: MCPProtocol(session_id='prod'), Scope.SINGLETON)

# Step 4: Register production agents
def create_production_agent(env, mcp):
    return ProductionAgent(
        name='prod_agent',
        config={
            'api_key': env.get('AGENT_API_KEY'),
            'port': env.get_int('AGENT_PORT')
        },
        mcp=mcp
    )

autowire.register('prod_agent', create_production_agent, Scope.SINGLETON)

# Step 5: Health check endpoint
class HealthCheckAgent(BaseAgent):
    async def execute(self, task: str, context: AgentContext):
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        }

autowire.register('health', lambda: HealthCheckAgent('health'), Scope.SINGLETON)

# Step 6: Start production system
logger.info("Starting production agent system...")
prod_agent = autowire.resolve('prod_agent')
health_agent = autowire.resolve('health')

# Verify health
context = AgentContext(session_id='prod_startup')
health = await health_agent.execute('check', context)
logger.info(f"System health: {health['status']}")
```

**What You Learned**:
- ✅ Production logging configuration
- ✅ Environment validation
- ✅ Dependency management
- ✅ Health checks
- ✅ Production deployment patterns

---

## Best Practices

### Key Takeaways from All Journeys

#### 1. **Always Use Contexts**
```python
# ✅ Good
context = AgentContext(
    session_id='unique_id',
    user_id='user_123',
    metadata={'source': 'api'}
)
result = await agent.execute(task, context)

# ❌ Bad
result = await agent.execute(task, None)
```

#### 2. **Configure Through Environment**
```python
# ✅ Good
config = {
    'model': env.get('MODEL'),
    'temperature': env.get_float('TEMPERATURE')
}
agent = MyAgent('agent', config)

# ❌ Bad
agent = MyAgent('agent', {'model': 'gpt-4'})  # Hardcoded
```

#### 3. **Use Dependency Injection**
```python
# ✅ Good
autowire.register('service', ServiceClass, Scope.SINGLETON)
autowire.register('agent', lambda service: Agent(service))

# ❌ Bad
service = ServiceClass()
agent = Agent(service)  # Manual wiring
```

#### 4. **Implement Error Handling**
```python
# ✅ Good
async def execute(self, task, context):
    try:
        return await self._primary_method(task)
    except Exception as e:
        self.log_error(f"Error: {e}")
        return await self._fallback_method(task)

# ❌ Bad
async def execute(self, task, context):
    return await self._risky_method(task)  # No error handling
```

#### 5. **Log Everything Important**
```python
# ✅ Good
self.log_info(f"Starting task: {task}")
result = await self.process(task)
self.log_info(f"Completed task: {task}")

# ❌ Bad
result = await self.process(task)  # Silent execution
```

---

## Quick Reference

### Common Patterns

| Pattern | Use Case | Example |
|---------|----------|---------|
| Single Agent | Simple task execution | Research, Analysis |
| Multi-Agent | Complex workflows | Research → Analysis → Report |
| Coordinator | Agent orchestration | Workflow management |
| MCP Integration | Standardized communication | Chat interfaces |
| Dependency Injection | Service management | Database, Logging, Config |
| Skills System | Reusable capabilities | Search, Summarize, Translate |

### Scope Guidelines

| Scope | Lifetime | Use For |
|-------|----------|---------|
| SINGLETON | Single instance | Services, Managers, Protocols |
| TRANSIENT | New instance each time | Request handlers, Temporary agents |
| SCOPED | Within a scope | Request-scoped resources |

---

## Next Steps

1. **Try the Examples**: Run examples in `/examples` directory
2. **Read the Docs**: Check [AGENT.md](./AGENT.md) and [SKILLS.md](./SKILLS.md)
3. **Run Tests**: Execute `pytest tests/test_user_journey.py -v`
4. **Build Your Agent**: Start with Journey 1 and progress
5. **Join Community**: Share your experiences and learn from others

---

## Support

- **Documentation**: See [README.md](./README.md)
- **Examples**: Check `/examples` directory
- **Tests**: Review `/tests` for more patterns
- **Issues**: Report bugs and request features

---

**Made with ❤️ for the AI agent development community**
