# 🤖 AGENT.md - AI Agent Development Guide

> Comprehensive guide for building, configuring, and deploying AI agents with auto-wiring

## Table of Contents

1. [Introduction](#introduction)
2. [Agent Architecture](#agent-architecture)
3. [Quick Start](#quick-start)
4. [Agent Types](#agent-types)
5. [Auto-Wiring Integration](#auto-wiring-integration)
6. [Configuration](#configuration)
7. [Skills & Capabilities](#skills--capabilities)
8. [MCP Integration](#mcp-integration)
9. [State Management](#state-management)
10. [Error Handling](#error-handling)
11. [Testing](#testing)
12. [Best Practices](#best-practices)
13. [Advanced Topics](#advanced-topics)

---

## Introduction

The AI Auto-Wiring System provides a revolutionary framework for building intelligent agents with automatic dependency injection, configuration management, and seamless integration with various AI services.

### Key Features

- **🔌 Auto-Wiring**: Automatic dependency injection for all agent components
- **⚙️ Configuration Management**: Multi-source configuration with validation
- **🤖 MCP Protocol**: Standardized communication via Model Context Protocol
- **🧠 Skills Registry**: Dynamic capability management and discovery
- **🔒 SSH Integration**: Secure remote execution capabilities
- **📊 State Management**: Persistent and distributed state handling
- **🔄 Hot Reloading**: Dynamic agent updates without restart
- **🧪 Testing Framework**: Comprehensive testing utilities

---

## Agent Architecture

### Component Hierarchy

```
┌─────────────────────────────────────────┐
│           Agent Interface               │
│  (BaseAgent, Task, Context)             │
└──────────────┬──────────────────────────┘
               │
     ┌─────────┴─────────┐
     │                   │
┌────▼────┐       ┌─────▼──────┐
│ Skills  │       │   State    │
│Registry │       │  Manager   │
└────┬────┘       └─────┬──────┘
     │                  │
     └──────┬───────────┘
            │
      ┌─────▼─────┐
      │ Auto-Wire │
      │  Engine   │
      └───────────┘
```

### Core Components

1. **BaseAgent**: Abstract base class for all agents
2. **AgentContext**: Execution context with state and configuration
3. **SkillRegistry**: Dynamic capability management
4. **StateManager**: Persistent state handling
5. **MCPProtocol**: Communication protocol
6. **AutoWire**: Dependency injection engine

---

## Quick Start

### 1. Create a Basic Agent

```python
from src.agents.base_agent import BaseAgent, AgentContext
from src.core.autowire import AutoWire, inject

class MyAgent(BaseAgent):
    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)
        self.model = config.get('model', 'gpt-4')
    
    async def execute(self, task: str, context: AgentContext) -> dict:
        """Execute agent task"""
        self.log_info(f"Executing task: {task}")
        
        # Your agent logic here
        result = await self.process_task(task, context)
        
        return {
            'success': True,
            'result': result,
            'agent': self.name
        }
    
    async def process_task(self, task: str, context: AgentContext):
        # Implement your task processing logic
        return f"Processed: {task}"
```

### 2. Register with Auto-Wiring

```python
from src.core.autowire import get_autowire, Scope

autowire = get_autowire()

# Register agent factory
autowire.register(
    name='my_agent',
    factory=lambda: MyAgent('my_agent', {'model': 'gpt-4'}),
    scope=Scope.SINGLETON,
    tags=['agent', 'processing']
)

# Resolve and use agent
agent = autowire.resolve('my_agent')
```

### 3. Execute Tasks

```python
import asyncio
from src.agents.base_agent import AgentContext

async def main():
    # Create context
    context = AgentContext(
        session_id='session_123',
        user_id='user_456',
        metadata={'priority': 'high'}
    )
    
    # Execute task
    result = await agent.execute("Analyze data", context)
    print(result)

asyncio.run(main())
```

---

## Agent Types

### 1. Research Agent

Specializes in information gathering and analysis.

```python
class ResearchAgent(BaseAgent):
    """Agent for research and information gathering"""
    
    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)
        self.sources = config.get('sources', [])
        self.max_depth = config.get('max_depth', 3)
    
    async def execute(self, task: str, context: AgentContext) -> dict:
        # Implement research logic
        findings = await self.research(task, context)
        summary = await self.summarize(findings)
        
        return {
            'success': True,
            'findings': findings,
            'summary': summary
        }
```

### 2. Execution Agent

Handles code execution and system operations.

```python
class ExecutionAgent(BaseAgent):
    """Agent for executing code and system commands"""
    
    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)
        self.ssh_manager = None  # Injected via autowire
    
    async def execute(self, task: str, context: AgentContext) -> dict:
        # Parse and validate command
        command = self.parse_command(task)
        
        # Execute with safety checks
        result = await self.safe_execute(command, context)
        
        return result
```

### 3. Coordination Agent

Orchestrates multiple sub-agents.

```python
class CoordinationAgent(BaseAgent):
    """Agent for orchestrating multiple agents"""
    
    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)
        self.sub_agents = []
    
    async def execute(self, task: str, context: AgentContext) -> dict:
        # Decompose task
        sub_tasks = self.decompose_task(task)
        
        # Distribute to sub-agents
        results = await self.execute_parallel(sub_tasks, context)
        
        # Aggregate results
        final_result = self.aggregate_results(results)
        
        return final_result
```

---

## Auto-Wiring Integration

### Dependency Injection

```python
from src.core.autowire import inject, AutoWire

class MyAgent(BaseAgent):
    def __init__(
        self,
        name: str,
        config_loader,  # Auto-injected
        mcp_protocol,   # Auto-injected
        ssh_manager     # Auto-injected
    ):
        super().__init__(name)
        self.config_loader = config_loader
        self.mcp = mcp_protocol
        self.ssh = ssh_manager

# Register with dependencies
autowire = AutoWire()

autowire.register('config_loader', ConfigLoader)
autowire.register('mcp_protocol', MCPProtocol)
autowire.register('ssh_manager', SSHManager)

# Agent will automatically receive dependencies
autowire.register('my_agent', MyAgent)
agent = autowire.resolve('my_agent')
```

### Decorator-Based Registration

```python
from src.core.autowire import get_autowire, Scope

autowire = get_autowire()

@autowire.register_decorator(
    name='smart_agent',
    scope=Scope.SINGLETON,
    tags=['intelligent', 'autonomous']
)
class SmartAgent(BaseAgent):
    pass
```

---

## Configuration

### Agent Configuration Structure

```json
{
  "agents": {
    "research_agent": {
      "enabled": true,
      "model": "gpt-4",
      "temperature": 0.7,
      "max_tokens": 4096,
      "timeout": 30,
      "skills": ["search", "summarize", "analyze"],
      "sources": ["web", "database", "api"]
    },
    "execution_agent": {
      "enabled": true,
      "sandbox": true,
      "allowed_commands": ["ls", "cat", "grep"],
      "ssh": {
        "enabled": true,
        "default_host": "localhost",
        "timeout": 30
      }
    }
  }
}
```

### Loading Configuration

```python
from src.config import get_config_loader

# Load agent configuration
config_loader = get_config_loader()
agent_config = config_loader.get('agents.research_agent')

# Create agent with config
agent = ResearchAgent('research', agent_config)
```

### Environment Variables

```bash
# Agent configuration via environment
AI_AGENTS_RESEARCH_AGENT_MODEL=gpt-4
AI_AGENTS_RESEARCH_AGENT_TEMPERATURE=0.7
AI_AGENTS_EXECUTION_AGENT_SANDBOX=true
```

---

## Skills & Capabilities

### Defining Skills

```python
from src.agents.skills import Skill, SkillRegistry

class SearchSkill(Skill):
    """Web search capability"""
    
    def __init__(self):
        super().__init__(
            name='search',
            description='Search the web for information',
            category='research',
            parameters={
                'query': {'type': 'string', 'required': True},
                'max_results': {'type': 'integer', 'default': 10}
            }
        )
    
    async def execute(self, query: str, max_results: int = 10):
        # Implement search logic
        results = await self.perform_search(query, max_results)
        return results
```

### Registering Skills

```python
# Create skill registry
registry = SkillRegistry()

# Register skills
registry.register(SearchSkill())
registry.register(SummarizeSkill())
registry.register(AnalyzeSkill())

# Add skills to agent
agent.add_skills(registry.get_by_category('research'))
```

### Using Skills

```python
class MyAgent(BaseAgent):
    async def execute(self, task: str, context: AgentContext) -> dict:
        # Use registered skill
        if self.has_skill('search'):
            search_results = await self.use_skill(
                'search',
                query=task,
                max_results=10
            )
            
            return {'results': search_results}
```

See [SKILLS.md](./SKILLS.md) for complete skills reference.

---

## MCP Integration

### Using MCP Protocol

```python
from src.mcp import MCPProtocol, MCPRole, MCPMessageType

class MCPAgent(BaseAgent):
    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)
        self.mcp = MCPProtocol(session_id=f"agent_{name}")
    
    async def execute(self, task: str, context: AgentContext) -> dict:
        # Send request via MCP
        message = self.mcp.send(
            content=task,
            role=MCPRole.USER,
            message_type=MCPMessageType.REQUEST
        )
        
        # Process and respond
        response = await self.process_mcp_message(message)
        
        return {'message_id': message.id, 'response': response}
```

### MCP Message Handling

```python
from src.mcp import MCPHandler, MCPMessage, MCPContext

class AgentMCPHandler(MCPHandler):
    def __init__(self, agent: BaseAgent):
        self.agent = agent
    
    def can_handle(self, message: MCPMessage, context: MCPContext) -> bool:
        return message.type == MCPMessageType.REQUEST
    
    def handle(self, message: MCPMessage, context: MCPContext):
        # Handle message with agent
        result = self.agent.execute_sync(message.content)
        
        # Create response
        return MCPMessage(
            id=f"resp_{message.id}",
            type=MCPMessageType.RESPONSE,
            role=MCPRole.ASSISTANT,
            content=result,
            parent_id=message.id
        )
```

---

## State Management

### Persistent State

```python
class StatefulAgent(BaseAgent):
    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)
        self.state_manager = StateManager(agent_name=name)
    
    async def execute(self, task: str, context: AgentContext) -> dict:
        # Load state
        state = await self.state_manager.load()
        
        # Execute with state
        result = await self.process_with_state(task, state, context)
        
        # Save updated state
        await self.state_manager.save(state)
        
        return result
```

### Distributed State

```python
from src.agents.state import DistributedStateManager

class DistributedAgent(BaseAgent):
    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)
        self.state = DistributedStateManager(
            agent_name=name,
            backend='redis',
            ttl=3600
        )
    
    async def execute(self, task: str, context: AgentContext) -> dict:
        # Acquire distributed lock
        async with self.state.lock(f"task_{task}"):
            # Process with exclusive access
            result = await self.process_exclusive(task, context)
        
        return result
```

---

## Error Handling

### Retry Mechanism

```python
from src.agents.decorators import retry, timeout

class RobustAgent(BaseAgent):
    @retry(max_attempts=3, backoff=2.0)
    @timeout(seconds=30)
    async def execute(self, task: str, context: AgentContext) -> dict:
        # This will retry up to 3 times with exponential backoff
        # and timeout after 30 seconds
        result = await self.risky_operation(task)
        return result
```

### Error Recovery

```python
class RecoverableAgent(BaseAgent):
    async def execute(self, task: str, context: AgentContext) -> dict:
        try:
            result = await self.primary_method(task, context)
        except PrimaryMethodError as e:
            self.log_warning(f"Primary method failed: {e}")
            result = await self.fallback_method(task, context)
        except Exception as e:
            self.log_error(f"Unhandled error: {e}")
            result = self.default_response()
        
        return result
```

---

## Testing

### Unit Testing

```python
import pytest
from src.agents.base_agent import AgentContext

@pytest.mark.asyncio
async def test_agent_execution():
    # Create agent
    agent = MyAgent('test_agent', {'model': 'gpt-4'})
    
    # Create context
    context = AgentContext(session_id='test_123')
    
    # Execute task
    result = await agent.execute("test task", context)
    
    # Assertions
    assert result['success'] is True
    assert 'result' in result
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_multi_agent_coordination():
    # Setup agents
    coordinator = CoordinationAgent('coordinator')
    worker1 = WorkerAgent('worker1')
    worker2 = WorkerAgent('worker2')
    
    coordinator.add_sub_agent(worker1)
    coordinator.add_sub_agent(worker2)
    
    # Execute coordinated task
    context = AgentContext(session_id='test_456')
    result = await coordinator.execute("complex task", context)
    
    # Verify coordination
    assert len(result['sub_results']) == 2
```

---

## Best Practices

### 1. **Single Responsibility**
Each agent should have one clear purpose.

✅ **Good:**
```python
class DataAnalysisAgent(BaseAgent):
    """Focused on data analysis only"""
    pass
```

❌ **Bad:**
```python
class SuperAgent(BaseAgent):
    """Does everything: analysis, execution, communication, etc."""
    pass
```

### 2. **Configuration Over Code**
Use configuration files for agent behavior.

✅ **Good:**
```python
agent = MyAgent('agent', config={
    'model': 'gpt-4',
    'temperature': 0.7,
    'max_retries': 3
})
```

### 3. **Async by Default**
Use async/await for all I/O operations.

✅ **Good:**
```python
async def execute(self, task: str, context: AgentContext):
    result = await self.async_operation()
    return result
```

### 4. **Comprehensive Logging**
Log all important operations.

```python
self.log_info("Starting task execution")
self.log_debug(f"Task details: {task}")
self.log_error(f"Execution failed: {error}")
```

### 5. **Graceful Degradation**
Always provide fallback behavior.

```python
try:
    result = await self.preferred_method()
except Exception:
    result = await self.fallback_method()
```

---

## Advanced Topics

### Multi-Agent Systems

```python
class AgentNetwork:
    """Network of cooperating agents"""
    
    def __init__(self):
        self.agents = {}
        self.message_bus = MessageBus()
    
    def add_agent(self, agent: BaseAgent):
        self.agents[agent.name] = agent
        agent.connect(self.message_bus)
    
    async def broadcast(self, message: dict):
        for agent in self.agents.values():
            await agent.receive_broadcast(message)
```

### Agent Learning

```python
class LearningAgent(BaseAgent):
    """Agent that learns from experience"""
    
    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)
        self.experience_buffer = []
        self.model = self.load_model()
    
    async def execute(self, task: str, context: AgentContext) -> dict:
        # Execute task
        result = await self.process(task, context)
        
        # Store experience
        self.experience_buffer.append({
            'task': task,
            'result': result,
            'context': context
        })
        
        # Periodic learning
        if len(self.experience_buffer) >= 100:
            await self.learn()
        
        return result
    
    async def learn(self):
        # Implement learning logic
        pass
```

### Remote Agent Deployment

```python
class RemoteAgent(BaseAgent):
    """Agent deployed on remote server via SSH"""
    
    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)
        self.ssh_manager = SSHManager()
    
    async def deploy(self, host: str):
        # Upload agent code
        await self.ssh_manager.upload_file(
            local_path=Path(__file__),
            remote_path=f'/opt/agents/{self.name}.py',
            credentials=self.get_ssh_credentials(host)
        )
        
        # Start agent
        result = await self.ssh_manager.execute(
            command=f'python /opt/agents/{self.name}.py start',
            credentials=self.get_ssh_credentials(host)
        )
        
        return result.success
```

---

## Examples

See the `examples/` directory for complete examples:

- `examples/basic_agent.py` - Simple agent implementation
- `examples/research_agent.py` - Research agent with web search
- `examples/multi_agent.py` - Multi-agent coordination
- `examples/mcp_agent.py` - MCP protocol integration
- `examples/remote_agent.py` - Remote deployment

---

## API Reference

### BaseAgent

```python
class BaseAgent:
    def __init__(self, name: str, config: dict = None)
    async def execute(self, task: str, context: AgentContext) -> dict
    def add_skill(self, skill: Skill)
    def has_skill(self, skill_name: str) -> bool
    async def use_skill(self, skill_name: str, **kwargs) -> Any
    def log_info(self, message: str)
    def log_warning(self, message: str)
    def log_error(self, message: str)
```

### AgentContext

```python
@dataclass
class AgentContext:
    session_id: str
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
```

---

## Troubleshooting

### Common Issues

1. **Agent Not Registered**
   - Ensure agent is registered with AutoWire before resolving
   - Check for circular dependencies

2. **Configuration Not Loading**
   - Verify config file path and format
   - Check environment variable naming

3. **MCP Communication Errors**
   - Ensure MCP protocol is initialized
   - Verify message format and handlers

---

## Contributing

See the main README for contribution guidelines.

---

## License

MIT License - See LICENSE file for details.

---

**Made with ❤️ for intelligent AI development**
