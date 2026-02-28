# 🤖 CLAUDE.md - AI Assistant Guide for WIREDUP

> Comprehensive guide for AI assistants working with the WIREDUP codebase

**Last Updated**: 2026-01-18
**Version**: 1.0.0

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Codebase Structure](#codebase-structure)
3. [Architecture & Key Components](#architecture--key-components)
4. [Development Workflows](#development-workflows)
5. [Coding Conventions](#coding-conventions)
6. [Configuration Management](#configuration-management)
7. [Testing Strategy](#testing-strategy)
8. [Git Workflow](#git-workflow)
9. [Common Tasks](#common-tasks)
10. [Important Files](#important-files)
11. [Dependencies](#dependencies)
12. [AI Assistant Guidelines](#ai-assistant-guidelines)

---

## Project Overview

WIREDUP is a **Revolutionary AI Auto-Wiring System** that provides intelligent dependency injection for AI agents with comprehensive environment management, MCP integration, and SSH capabilities.

### Technology Stack

**Primary Languages:**
- **Python 3.8+**: Core auto-wiring system (20 source files)
- **Rust 1.75+**: High-performance terminal implementation (19 source files)

**Key Frameworks:**
- Python: asyncio, paramiko, structlog, pytest
- Rust: tokio, ratatui, crossterm, serde

### Project Type
Dual-language hybrid system combining:
1. **Python Auto-Wiring Engine**: Dependency injection framework for AI agents
2. **Rust Terminal (NexTerm)**: Modern terminal with AI integration bridge

### License
MIT License

---

## Codebase Structure

```
/home/user/WIREDUP/
├── .claude/                      # Claude AI agent configurations
│   ├── agents/kfc/              # KFC spec-based agent definitions
│   ├── settings/                # Claude-specific settings
│   └── system-prompts/          # System prompt templates
│
├── .cursor/                      # Cursor IDE rules
│   └── rules/after_each_chat.mdc
│
├── src/                          # Python source code
│   ├── core/                    # Core auto-wiring system
│   │   ├── autowire.py          # DI engine (355 lines)
│   │   └── registry.py          # Service/component registries
│   ├── agents/                  # Agent framework
│   │   └── base_agent.py        # Abstract base agent
│   ├── config/                  # Configuration system
│   │   ├── loader.py            # Hierarchical config loading
│   │   └── env_manager.py       # Environment management
│   ├── mcp/                     # Model Context Protocol
│   │   └── protocol.py          # MCP implementation
│   ├── ssh/                     # SSH management
│   │   └── manager.py           # Connection pooling
│   └── cli.py                   # CLI interface
│
├── rust-terminal/               # Rust terminal (NexTerm)
│   ├── src/
│   │   ├── ai/                  # AI integration
│   │   │   ├── autowire_bridge.rs  # Python ↔ Rust bridge
│   │   │   ├── nlp.rs           # NLP processing
│   │   │   └── suggestions.rs   # AI command suggestions
│   │   ├── core/                # Terminal engine
│   │   │   ├── terminal.rs      # Main terminal logic
│   │   │   ├── executor.rs      # Command executor
│   │   │   └── command.rs       # Command parser
│   │   ├── plugins/             # Plugin system
│   │   │   ├── manager.rs       # Plugin manager
│   │   │   └── builtin.rs       # Built-in plugins
│   │   ├── ui/                  # Terminal UI
│   │   │   ├── tui.rs           # TUI implementation
│   │   │   ├── widgets.rs       # Custom widgets
│   │   │   └── themes.rs        # Theme system
│   │   ├── utils/               # Utilities
│   │   │   ├── config.rs        # Config management
│   │   │   └── history.rs       # Command history
│   │   └── main.rs              # Entry point
│   └── Cargo.toml               # Rust dependencies
│
├── tests/                       # Python tests
│   ├── test_autowire.py         # Core auto-wire tests
│   └── test_autowire_unittest.py
│
├── examples/                    # Example implementations
│   ├── basic_agent.py           # Basic agent usage
│   ├── mcp_integration.py       # MCP example
│   └── ssh_deployment.py        # SSH deployment
│
├── config/                      # Configuration files
│   └── default.json             # Default configuration
│
├── public/                      # Public assets
│   └── index.html
│
├── .snapshots/                  # Documentation snapshots
│
├── requirements.txt             # Python dependencies
├── setup.py                     # Python package setup
├── Cargo.toml                   # Workspace Rust config
│
└── Documentation Files:
    ├── README.md                # Main documentation
    ├── AGENT.md                 # Agent development guide
    ├── SKILLS.md                # Skills reference
    ├── QUICKSTART.md            # Quick start guide
    ├── DEPLOYMENT.md            # Deployment instructions
    ├── CLOUDFLARE_DEPLOY.md     # Cloudflare deployment
    ├── GITHUB_PUSH.md           # GitHub deployment
    └── VERIFICATION_*.md        # Verification reports
```

---

## Architecture & Key Components

### 1. Python Auto-Wiring System

#### AutoWire Engine (`src/core/autowire.py`)
**Purpose**: Revolutionary dependency injection system for AI agents

**Key Features**:
- Three lifecycle scopes: **Singleton**, **Transient**, **Scoped**
- Automatic dependency resolution from function signatures
- Circular dependency detection with clear error messages
- Type-based and name-based injection
- Tag-based service location
- Lazy initialization support
- Thread-safe operations with RLock
- Decorator-based registration

**Critical Implementation Details**:
```python
# Three scopes with different lifecycles
class Scope(Enum):
    SINGLETON = "singleton"  # One instance, reused
    TRANSIENT = "transient"  # New instance each resolve
    SCOPED = "scoped"        # Per-scope instance

# Global instance available
_global_autowire: Optional[AutoWire] = None

def get_autowire() -> AutoWire:
    """Get or create global autowire instance"""
```

**Usage Pattern**:
```python
# Registration
autowire.register(
    name='service_name',
    factory=lambda: ServiceClass(),
    scope=Scope.SINGLETON,
    tags=['tag1', 'tag2']
)

# Resolution
service = autowire.resolve('service_name')

# Decorator-based
@autowire.register_decorator(name='my_service', scope=Scope.SINGLETON)
class MyService:
    pass
```

#### Service Registry (`src/core/registry.py`)
**Purpose**: Dual registry system for services and components

**ServiceRegistry Features**:
- Runtime service registration with health checks
- Type indexing for fast lookups
- Capability-based service discovery
- Health check monitoring

**ComponentRegistry Features**:
- Pluggable component management
- Priority-based execution
- Dependency management with topological sort
- Component lifecycle hooks

#### Configuration System (`src/config/`)

**ConfigLoader** (`loader.py`):
- **Load Order** (priority low to high):
  1. `config/default.json`
  2. `config/{env}.json`
  3. `config/local.json`
  4. `.env.{env}`, `.env.local`, `.env`
  5. Environment variables
  6. Command-line arguments
- Dot notation access: `config.get('mcp.port')`
- Deep merging of configurations
- Validation framework

**EnvManager** (`env_manager.py`):
- Multi-source environment loading
- Type conversion helpers (int, bool, list)
- Sensitive data masking in logs
- Hot-reloading support
- Variable expansion: `${VAR_NAME}`
- Pattern and choice validation

**Configuration Structure**:
```json
{
  "system": { ... },      // System metadata
  "autowire": { ... },    // Auto-wiring settings
  "mcp": { ... },         // MCP protocol config
  "ssh": { ... },         // SSH settings
  "agents": { ... },      // Agent configurations
  "skills": { ... },      // Skills registry
  "logging": { ... },     // Logging configuration
  "security": { ... }     // Security settings
}
```

#### Model Context Protocol (`src/mcp/protocol.py`)
**Purpose**: Standardized AI communication protocol

**Message Types**:
- `REQUEST`: Request for action
- `RESPONSE`: Response to request
- `NOTIFICATION`: One-way notification
- `ERROR`: Error message
- `STREAM`: Streaming data

**Roles**:
- `SYSTEM`: System messages
- `USER`: User messages
- `ASSISTANT`: AI assistant messages
- `TOOL`: Tool/function messages
- `AGENT`: Agent-to-agent messages

**Key Features**:
- Context management with message history
- Tool/function calling support
- Event hooks (before_send, after_send, etc.)
- Context export/import for persistence
- Message threading with parent_id

#### SSH Management (`src/ssh/manager.py`)
**Purpose**: Secure remote execution and file operations

**SSHConnectionPool**:
- Thread-safe connection pooling
- Connection reuse with automatic cleanup
- Connection aging and idle timeout
- Credential management

**SSHManager Features**:
- Command execution with retries
- File transfer via SFTP
- Batch and parallel execution
- Context manager support

#### Base Agent Framework (`src/agents/base_agent.py`)
**Purpose**: Foundation for all AI agents

**Features**:
- Abstract base class with logging
- Skill management system
- Configuration management
- Execution context handling
- Async execution support

**Required Implementations**:
```python
class MyAgent(BaseAgent):
    async def execute(self, task: str, context: AgentContext) -> dict:
        """Must be implemented by subclasses"""
        pass
```

### 2. Rust Terminal (NexTerm)

#### Auto-Wiring Bridge (`rust-terminal/src/ai/autowire_bridge.rs`)
**Purpose**: Connect Rust terminal to Python auto-wiring system

**How It Works**:
1. Detects Python availability on system
2. Spawns Python subprocess for auto-wiring operations
3. Communicates via JSON serialization
4. Caches results for performance
5. Graceful fallback when Python unavailable

**Key Functions**:
```rust
pub fn new() -> Self
pub fn is_available(&self) -> bool
pub fn process_command(&self, command: &str) -> Option<String>
pub fn get_suggestion(&self, partial: &str) -> Option<String>
pub fn count_services(&self) -> usize
```

#### Terminal Core (`rust-terminal/src/core/terminal.rs`)
**Purpose**: Main terminal engine with async execution

**Features**:
- Tokio-based async runtime
- Command execution with timing
- Output buffering with Arc<Mutex<>>
- Command history tracking
- Background process support
- Auto-wiring integration hooks

#### Plugin System (`rust-terminal/src/plugins/`)
**Purpose**: Extensible plugin architecture

**Built-in Plugins**:
- Git operations
- Docker management
- Kubernetes integration
- AWS CLI helpers

**Plugin Interface**:
```rust
pub trait Plugin {
    fn name(&self) -> &str;
    fn execute(&self, args: &[String]) -> Result<String>;
    fn help(&self) -> String;
}
```

#### Terminal UI (`rust-terminal/src/ui/`)
**Purpose**: Modern TUI with ratatui

**Features**:
- Split panes and tabs
- Syntax highlighting with syntect
- Customizable themes
- Status bar and widgets
- Fuzzy finder (Ctrl+R)
- History search

---

## Development Workflows

### Python Development

#### Setting Up Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

#### Running the System

```bash
# Initialize system
python -m src.cli init

# Start auto-wiring system
python -m src.cli start

# Check status
python -m src.cli status

# Create agent
python -m src.cli create-agent research_agent

# List components
python -m src.cli list-components

# Show version
python -m src.cli version
```

#### Code Quality Tools

```bash
# Format code with black
black src/ tests/

# Lint with flake8
flake8 src/ tests/

# Type check with mypy
mypy src/

# Run all quality checks
black src/ tests/ && flake8 src/ tests/ && mypy src/
```

### Rust Development

#### Building

```bash
cd rust-terminal

# Debug build
cargo build

# Release build (optimized)
cargo build --release

# Check without building
cargo check
```

#### Running

```bash
# Run in debug mode
cargo run

# Run release build
cargo run --release

# Run example
cargo run --example simple
```

#### Code Quality

```bash
# Format code
cargo fmt

# Lint with clippy (deny warnings in CI)
cargo clippy -- -D warnings

# Run all checks
cargo fmt && cargo clippy -- -D warnings && cargo test
```

### Testing

#### Python Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_autowire.py

# Run specific test
pytest tests/test_autowire.py::TestAutoWire::test_singleton_scope

# Run with verbose output
pytest -v

# Run async tests
pytest tests/ -v --asyncio-mode=auto
```

**Test Structure** (`tests/test_autowire.py`):
- `TestAutoWire`: Dependency injection tests
- `TestEnvManager`: Configuration tests
- `TestMCPProtocol`: Protocol tests
- `TestBaseAgent`: Agent framework tests
- `TestIntegration`: Full stack integration tests

#### Rust Tests

```bash
# Run all tests
cargo test

# Run with output
cargo test -- --nocapture

# Run specific test
cargo test test_autowire_bridge

# Run with verbose
cargo test --verbose
```

---

## Coding Conventions

### Python Conventions

#### Naming

```python
# Functions and variables: snake_case
def process_request(user_id: str) -> dict:
    result_data = {}

# Classes: PascalCase
class AutoWireEngine:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# Private members: leading underscore
class MyClass:
    def __init__(self):
        self._internal_state = {}

    def _private_method(self):
        pass
```

#### Type Hints

```python
from typing import Optional, Dict, List, Any

# Always use type hints
def process_data(
    data: Dict[str, Any],
    timeout: Optional[int] = None
) -> List[str]:
    pass

# Use dataclasses for data structures
from dataclasses import dataclass, field

@dataclass
class AgentContext:
    session_id: str
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

#### Async Pattern

```python
# Prefer async/await for I/O operations
async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# Use asyncio for concurrent operations
results = await asyncio.gather(
    fetch_data(url1),
    fetch_data(url2),
    fetch_data(url3)
)
```

#### Error Handling

```python
# Specific exceptions first, then general
try:
    result = await process()
except SpecificError as e:
    logger.warning(f"Specific error: {e}")
    result = fallback_method()
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise

# Use context managers for resource cleanup
async with connection_pool.acquire() as conn:
    result = await conn.execute(query)
```

#### Logging

```python
# Use structlog with appropriate levels
logger.debug("Detailed debug info", extra_data=data)
logger.info("Normal operation", operation="start")
logger.warning("Potential issue", reason="timeout")
logger.error("Error occurred", error=str(e), traceback=True)
```

#### Docstrings

```python
def complex_function(arg1: str, arg2: int) -> dict:
    """
    One-line summary of function.

    Detailed description of what the function does,
    its purpose, and any important behavior.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Raises:
        ValueError: When invalid input provided
        ConnectionError: When connection fails

    Example:
        >>> result = complex_function("test", 42)
        >>> print(result)
        {'status': 'success'}
    """
    pass
```

### Rust Conventions

#### Naming

```rust
// Functions and variables: snake_case
fn process_command(input: &str) -> Result<String> {
    let result_data = String::new();
}

// Types and traits: PascalCase
struct AutoWireBridge {
    python_path: String,
}

trait Plugin {
    fn execute(&self) -> Result<()>;
}

// Constants: UPPER_SNAKE_CASE
const MAX_RETRIES: u32 = 3;
const DEFAULT_TIMEOUT: u64 = 30;

// Module names: snake_case
mod autowire_bridge;
mod command_parser;
```

#### Error Handling

```rust
// Use Result and ? operator
fn process() -> Result<String, Error> {
    let data = read_file()?;
    let parsed = parse_data(&data)?;
    Ok(parsed)
}

// Use anyhow for application errors
use anyhow::{Context, Result};

fn complex_operation() -> Result<()> {
    let data = read_file()
        .context("Failed to read configuration file")?;
    Ok(())
}

// Use thiserror for library errors
use thiserror::Error;

#[derive(Error, Debug)]
enum MyError {
    #[error("Configuration error: {0}")]
    Config(String),

    #[error("IO error")]
    Io(#[from] std::io::Error),
}
```

#### Async Pattern

```rust
// Use tokio for async operations
use tokio::fs::File;
use tokio::io::AsyncReadExt;

async fn read_data(path: &str) -> Result<String> {
    let mut file = File::open(path).await?;
    let mut contents = String::new();
    file.read_to_string(&mut contents).await?;
    Ok(contents)
}

// Use tokio::spawn for concurrent tasks
let handle1 = tokio::spawn(async { task1().await });
let handle2 = tokio::spawn(async { task2().await });

let (result1, result2) = tokio::join!(handle1, handle2);
```

#### Documentation

```rust
/// One-line summary of function.
///
/// Detailed description of what the function does,
/// its purpose, and any important behavior.
///
/// # Arguments
///
/// * `input` - Description of input parameter
/// * `timeout` - Optional timeout in seconds
///
/// # Returns
///
/// Description of return value
///
/// # Errors
///
/// Returns error if:
/// * Input is invalid
/// * Connection fails
///
/// # Examples
///
/// ```
/// let result = process_command("test")?;
/// assert_eq!(result, "success");
/// ```
pub fn process_command(input: &str, timeout: Option<u64>) -> Result<String> {
    // Implementation
}
```

---

## Configuration Management

### Environment Variables

**Prefix Convention**: `AI_`

**Format**: `AI_SECTION_SUBSECTION_KEY`

**Examples**:
```bash
# MCP Configuration
AI_MCP_ENABLED=true
AI_MCP_PORT=3000
AI_MCP_HOST=localhost

# SSH Configuration
AI_SSH_KEY_PATH=~/.ssh/id_rsa
AI_SSH_TIMEOUT=30

# Agent Configuration
AI_AGENTS_RESEARCH_AGENT_MODEL=gpt-4
AI_AGENTS_RESEARCH_AGENT_TEMPERATURE=0.7

# Logging
AI_LOG_LEVEL=INFO
AI_LOG_FORMAT=json

# System
AI_ENV=development
```

### Configuration Files

**Priority Order** (highest last):
1. `config/default.json` - Base configuration
2. `config/{env}.json` - Environment-specific
3. `config/local.json` - Local overrides (not committed)
4. `.env` files - Environment variables
5. System environment variables
6. Command-line arguments

**Access Pattern**:
```python
from src.config import get_config_loader

config = get_config_loader()

# Dot notation access
port = config.get('mcp.port', default=3000)
model = config.get('agents.research_agent.model')

# Type-safe access
timeout = config.get_int('ssh.timeout', default=30)
enabled = config.get_bool('mcp.enabled', default=False)
hosts = config.get_list('ssh.allowed_hosts', default=[])
```

### Validation

```python
# In EnvManager
env_manager = EnvManager()

# Port validation
env_manager.set_validation_rule('mcp.port', {
    'type': 'port',
    'min': 1024,
    'max': 65535
})

# Choice validation
env_manager.set_validation_rule('log.level', {
    'type': 'choice',
    'choices': ['DEBUG', 'INFO', 'WARNING', 'ERROR']
})

# Pattern validation (regex)
env_manager.set_validation_rule('ssh.host', {
    'type': 'pattern',
    'pattern': r'^[\w\-\.]+$'
})
```

---

## Testing Strategy

### Test Organization

```
tests/
├── test_autowire.py              # Core auto-wire functionality
├── test_autowire_unittest.py     # Additional unit tests
├── test_config.py                # Configuration system
├── test_agents.py                # Agent framework
├── test_mcp.py                   # MCP protocol
└── test_integration.py           # Full integration tests
```

### Test Fixtures

```python
import pytest
from pathlib import Path

@pytest.fixture
def temp_config_dir(tmp_path):
    """Provide temporary config directory"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir

@pytest.fixture
def autowire_instance():
    """Provide fresh AutoWire instance"""
    from src.core.autowire import AutoWire
    return AutoWire()

@pytest.fixture
async def agent_context():
    """Provide agent execution context"""
    from src.agents.base_agent import AgentContext
    return AgentContext(
        session_id='test_session',
        user_id='test_user'
    )
```

### Test Patterns

**Unit Tests**:
```python
@pytest.mark.asyncio
async def test_singleton_scope(autowire_instance):
    """Test that singleton scope returns same instance"""
    # Register service
    autowire_instance.register(
        name='service',
        factory=lambda: object(),
        scope=Scope.SINGLETON
    )

    # Resolve twice
    instance1 = autowire_instance.resolve('service')
    instance2 = autowire_instance.resolve('service')

    # Should be same instance
    assert instance1 is instance2
```

**Integration Tests**:
```python
@pytest.mark.asyncio
async def test_full_agent_workflow():
    """Test complete agent workflow with autowire and MCP"""
    # Setup
    autowire = get_autowire()
    autowire.register('config_loader', ConfigLoader)
    autowire.register('mcp_protocol', MCPProtocol)

    # Create agent
    agent = ResearchAgent('research', config={})

    # Execute task
    context = AgentContext(session_id='test')
    result = await agent.execute("test task", context)

    # Verify
    assert result['success'] is True
```

### Coverage Goals

- **Minimum**: 80% code coverage
- **Target**: 90% code coverage
- **Critical Paths**: 100% coverage required
  - Core auto-wire logic
  - Configuration loading
  - Error handling paths

---

## Git Workflow

### Branch Strategy

**Main Branches**:
- `main` or `master`: Production-ready code
- `develop`: Integration branch for features

**Feature Branches**:
- Pattern: `feature/description`
- Example: `feature/add-redis-backend`

**Bug Fix Branches**:
- Pattern: `fix/description`
- Example: `fix/circular-dependency-detection`

**Claude AI Branches**:
- Pattern: `claude/description-{session_id}`
- Example: `claude/add-claude-documentation-7n5gu`
- Always develop on Claude-specific branches

### Commit Messages

**Format**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code restructuring
- `perf`: Performance improvement
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples**:
```bash
feat(autowire): add lazy initialization support

Add support for lazy initialization of services to defer
expensive operations until first use.

Closes #123

fix(ssh): handle connection timeout properly

Previously timeouts would cause uncaught exceptions.
Now properly catches and logs timeout errors.

docs: update AGENT.md with new examples

refactor(config): simplify environment variable parsing
```

### Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make Changes and Commit**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. **Push to Remote**
   ```bash
   git push -u origin feature/my-feature
   ```

4. **Create Pull Request**
   - Use GitHub UI or `gh` CLI
   - Provide clear description
   - Reference related issues
   - Include test results

5. **Code Review**
   - Address feedback
   - Update PR as needed

6. **Merge**
   - Squash commits if needed
   - Delete branch after merge

### Git Best Practices

```bash
# Always pull before pushing
git pull origin main

# Use rebase for clean history
git rebase main

# Interactive rebase to clean commits
git rebase -i HEAD~3

# Stash changes temporarily
git stash
git stash pop

# Check status frequently
git status

# View diff before committing
git diff
git diff --staged
```

---

## Common Tasks

### Adding a New Agent

1. **Create Agent Class**:
```python
# src/agents/my_agent.py
from src.agents.base_agent import BaseAgent, AgentContext

class MyAgent(BaseAgent):
    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)
        # Initialize agent-specific attributes

    async def execute(self, task: str, context: AgentContext) -> dict:
        # Implement agent logic
        return {'success': True, 'result': 'done'}
```

2. **Register with AutoWire**:
```python
# In your initialization code
from src.core.autowire import get_autowire

autowire = get_autowire()
autowire.register(
    name='my_agent',
    factory=lambda: MyAgent('my_agent', config={}),
    scope=Scope.SINGLETON
)
```

3. **Add Configuration**:
```json
// config/default.json
{
  "agents": {
    "my_agent": {
      "enabled": true,
      "model": "gpt-4",
      "timeout": 30
    }
  }
}
```

4. **Write Tests**:
```python
# tests/test_my_agent.py
@pytest.mark.asyncio
async def test_my_agent():
    agent = MyAgent('test', {})
    context = AgentContext(session_id='test')
    result = await agent.execute("task", context)
    assert result['success'] is True
```

### Adding a New Skill

1. **Create Skill Class**:
```python
# src/agents/skills/my_skill.py
from src.agents.skills import Skill, SkillContext

class MySkill(Skill):
    def __init__(self):
        super().__init__(
            name='my_skill',
            description='Does something useful',
            category='custom'
        )

    async def execute(self, context: SkillContext, **kwargs):
        # Implement skill logic
        return {'result': 'success'}
```

2. **Register Skill**:
```python
from src.agents.skills import SkillRegistry

registry = SkillRegistry()
registry.register(MySkill())
```

3. **Document in SKILLS.md**:
Add entry with parameters, returns, usage example, and categories.

### Adding Configuration Option

1. **Add to default config**:
```json
// config/default.json
{
  "my_section": {
    "new_option": "default_value"
  }
}
```

2. **Access in code**:
```python
from src.config import get_config_loader

config = get_config_loader()
value = config.get('my_section.new_option')
```

3. **Add environment variable support**:
```bash
# .env.example
AI_MY_SECTION_NEW_OPTION=value
```

### Running Integration Tests

```bash
# Run full test suite
pytest tests/

# Run only integration tests
pytest tests/test_integration.py

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run in parallel (faster)
pytest -n auto

# Run with detailed output
pytest -vv --tb=short
```

### Building Documentation

```bash
# Generate API docs (if sphinx is set up)
cd docs/
make html

# View documentation
open _build/html/index.html
```

### Deployment Tasks

See dedicated documentation:
- `DEPLOYMENT.md` - General deployment guide
- `CLOUDFLARE_DEPLOY.md` - Cloudflare deployment
- `GITHUB_PUSH.md` - GitHub deployment
- `QUICKSTART.md` - Quick start guide

---

## Important Files

### Configuration Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies |
| `setup.py` | Python package configuration |
| `Cargo.toml` | Rust workspace configuration |
| `rust-terminal/Cargo.toml` | Terminal dependencies |
| `.env.example` | Environment variable template |
| `config/default.json` | Default configuration |

### Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview and quick start |
| `AGENT.md` | Agent development guide |
| `SKILLS.md` | Skills reference and API |
| `CLAUDE.md` | This file - AI assistant guide |
| `DEPLOYMENT.md` | Deployment instructions |
| `QUICKSTART.md` | Quick start tutorial |

### Core Source Files

| File | Lines | Purpose |
|------|-------|---------|
| `src/core/autowire.py` | 355 | Dependency injection engine |
| `src/core/registry.py` | ~200 | Service/component registries |
| `src/config/loader.py` | ~250 | Configuration loading |
| `src/config/env_manager.py` | ~300 | Environment management |
| `src/mcp/protocol.py` | ~400 | MCP protocol implementation |
| `src/ssh/manager.py` | ~350 | SSH connection management |
| `src/agents/base_agent.py` | ~150 | Base agent class |

### Test Files

| File | Purpose |
|------|---------|
| `tests/test_autowire.py` | Core auto-wire tests (260 lines) |
| `tests/test_autowire_unittest.py` | Additional unit tests |

---

## Dependencies

### Python Dependencies

**Core Runtime**:
```
python>=3.8
paramiko>=3.0.0          # SSH protocol
python-dotenv>=1.0.0     # Environment files
pyyaml>=6.0              # YAML parsing
asyncio>=3.4.3           # Async runtime
aiofiles>=23.0.0         # Async file I/O
structlog>=23.1.0        # Structured logging
colorama>=0.4.6          # Terminal colors
typing-extensions>=4.5.0 # Type hints backport
```

**Development**:
```
pytest>=7.4.0            # Testing framework
pytest-asyncio>=0.21.0   # Async test support
pytest-cov>=4.1.0        # Coverage reporting
black>=23.7.0            # Code formatter
flake8>=6.1.0            # Linter
mypy>=1.5.0              # Type checker
```

**Optional** (commented in requirements.txt):
```
redis                    # Distributed state backend
boto3                    # AWS integration
requests                 # HTTP client
```

### Rust Dependencies

**Core Runtime**:
```toml
# Async
tokio = { version = "1.35", features = ["full"] }
async-trait = "0.1"

# UI
ratatui = "0.25"
crossterm = "0.27"
syntect = "5.1"
colored = "2.1"

# Serialization
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
toml = "0.8"

# Error Handling
anyhow = "1.0"
thiserror = "1.0"

# Logging
tracing = "0.1"
tracing-subscriber = "0.3"

# Networking
reqwest = { version = "0.11", features = ["json"] }

# File Operations
walkdir = "2.4"
notify = "6.1"

# Command Line
rustyline = "13.0"
shellexpand = "3.1"
regex = "1.10"
```

### Integration Points

**Python ↔ Rust Bridge**:
- Communication: Python subprocess + JSON
- Entry Point: `rust-terminal/src/ai/autowire_bridge.rs`
- Data Format: JSON serialization via serde

**External Services**:
- SSH servers (paramiko)
- Databases (optional: SQLAlchemy)
- Redis (optional: distributed state)
- AWS (optional: boto3)

---

## AI Assistant Guidelines

### Understanding the Codebase

1. **Start with Architecture**:
   - Read this CLAUDE.md file completely
   - Review README.md for project overview
   - Check AGENT.md and SKILLS.md for domain concepts

2. **Identify Components**:
   - Core auto-wire engine in `src/core/autowire.py`
   - Configuration in `src/config/`
   - Agents in `src/agents/`
   - Rust terminal in `rust-terminal/`

3. **Trace Data Flow**:
   - Configuration loading hierarchy
   - Dependency injection resolution
   - MCP message routing
   - Agent execution pipeline

### Making Changes

1. **Read Before Writing**:
   - ALWAYS read existing code before modifying
   - Understand patterns and conventions used
   - Check for similar implementations

2. **Follow Conventions**:
   - Use established naming patterns
   - Match existing code style
   - Add type hints (Python) or types (Rust)
   - Write docstrings/documentation

3. **Test Changes**:
   - Write tests for new functionality
   - Run existing tests to ensure no regressions
   - Aim for high coverage on new code

4. **Update Documentation**:
   - Update relevant .md files
   - Add docstrings to new functions/classes
   - Include usage examples

### Common Patterns to Recognize

**Dependency Injection**:
```python
# Pattern: Register then resolve
autowire.register('service', ServiceClass)
service = autowire.resolve('service')
```

**Configuration Access**:
```python
# Pattern: Dot notation with defaults
config.get('section.key', default=value)
```

**Async Operations**:
```python
# Pattern: async/await for I/O
async def operation():
    result = await async_call()
    return result
```

**Error Handling**:
```python
# Pattern: Specific then general
try:
    result = operation()
except SpecificError as e:
    handle_specific(e)
except Exception as e:
    handle_general(e)
```

**Logging**:
```python
# Pattern: Structured logging
logger.info("Operation", operation="start", param=value)
```

### Problem-Solving Approach

1. **Understand the Problem**:
   - Read error messages carefully
   - Check relevant documentation
   - Review related code

2. **Locate the Issue**:
   - Use grep/search to find relevant code
   - Trace execution path
   - Check configuration

3. **Design Solution**:
   - Consider existing patterns
   - Evaluate alternatives
   - Plan minimal change

4. **Implement and Test**:
   - Make focused changes
   - Add/update tests
   - Verify functionality

5. **Document**:
   - Update relevant docs
   - Add code comments if needed
   - Update CHANGELOG

### Best Practices for AI Assistants

**DO**:
- ✅ Read existing code before making changes
- ✅ Follow established patterns and conventions
- ✅ Write comprehensive tests
- ✅ Add clear documentation
- ✅ Use type hints and docstrings
- ✅ Handle errors gracefully
- ✅ Log important operations
- ✅ Keep changes focused and minimal
- ✅ Update relevant documentation files

**DON'T**:
- ❌ Guess at file locations or structure
- ❌ Skip reading existing implementations
- ❌ Ignore established conventions
- ❌ Make changes without tests
- ❌ Leave code undocumented
- ❌ Create duplicate functionality
- ❌ Over-engineer solutions
- ❌ Skip error handling
- ❌ Commit broken code

### Debugging Tips

**Python Debugging**:
```python
# Add debug logging
logger.debug("Value", value=value)

# Use pdb for interactive debugging
import pdb; pdb.set_trace()

# Check types
print(f"Type: {type(obj)}, Value: {obj}")

# Inspect object
print(dir(obj))
```

**Rust Debugging**:
```rust
// Add debug output
dbg!(value);

// Use debug trait
println!("{:?}", value);

// Pretty print
println!("{:#?}", value);

// Check types (won't compile, but shows type)
let _: () = value;
```

**Common Issues**:

1. **Import Errors**:
   - Check PYTHONPATH
   - Verify package installation
   - Check for circular imports

2. **Configuration Not Loading**:
   - Verify file paths
   - Check environment variables
   - Review load order

3. **Autowire Resolution Fails**:
   - Ensure service is registered
   - Check for circular dependencies
   - Verify factory function

4. **Async Issues**:
   - Ensure using await
   - Check event loop
   - Verify async context

### Working with This Project

**Initial Setup Checklist**:
- [ ] Read CLAUDE.md (this file)
- [ ] Review README.md
- [ ] Check AGENT.md and SKILLS.md
- [ ] Explore src/ directory structure
- [ ] Review test files in tests/
- [ ] Check configuration in config/
- [ ] Understand git workflow

**Before Making Changes**:
- [ ] Understand the requirement
- [ ] Read related code
- [ ] Check existing patterns
- [ ] Plan the approach
- [ ] Consider test strategy

**After Making Changes**:
- [ ] Run tests
- [ ] Check code quality (black, flake8, mypy)
- [ ] Update documentation
- [ ] Verify functionality
- [ ] Review git diff
- [ ] Write clear commit message

### Key Concepts to Master

1. **Dependency Injection**: Understand how AutoWire resolves and injects dependencies

2. **Configuration Hierarchy**: Know the loading order and priority

3. **MCP Protocol**: Understand message types, roles, and routing

4. **Agent Lifecycle**: Creation → Registration → Execution → Cleanup

5. **Skills System**: Registration → Discovery → Execution → Composition

6. **Async Patterns**: Proper use of async/await, asyncio.gather, etc.

7. **Error Handling**: Specific exceptions, logging, recovery strategies

8. **Testing Strategy**: Unit tests, integration tests, fixtures, mocking

---

## Quick Reference

### CLI Commands

```bash
# Python
python -m src.cli init              # Initialize system
python -m src.cli start             # Start system
python -m src.cli status            # Show status
python -m src.cli create-agent NAME # Create agent
python -m src.cli list-components   # List components

# Rust Terminal
cargo build                         # Build debug
cargo build --release               # Build release
cargo run                           # Run terminal
cargo test                          # Run tests

# Testing
pytest                              # Run all tests
pytest tests/test_autowire.py       # Run specific test
pytest --cov=src                    # With coverage

# Code Quality
black src/ tests/                   # Format Python
flake8 src/ tests/                  # Lint Python
mypy src/                           # Type check Python
cargo fmt                           # Format Rust
cargo clippy                        # Lint Rust
```

### Important Paths

```
/home/user/WIREDUP/                 # Project root
├── src/core/autowire.py            # DI engine
├── src/config/loader.py            # Config loading
├── src/agents/base_agent.py        # Base agent
├── tests/test_autowire.py          # Core tests
├── config/default.json             # Default config
└── rust-terminal/src/main.rs       # Terminal entry
```

### Key Classes

| Class | Module | Purpose |
|-------|--------|---------|
| `AutoWire` | `src.core.autowire` | Dependency injection |
| `ConfigLoader` | `src.config.loader` | Configuration loading |
| `EnvManager` | `src.config.env_manager` | Environment management |
| `MCPProtocol` | `src.mcp.protocol` | MCP protocol |
| `SSHManager` | `src.ssh.manager` | SSH management |
| `BaseAgent` | `src.agents.base_agent` | Agent base class |

### Environment Variables

```bash
AI_ENV=development                  # Environment name
AI_LOG_LEVEL=INFO                   # Log level
AI_MCP_ENABLED=true                 # Enable MCP
AI_MCP_PORT=3000                    # MCP port
AI_SSH_KEY_PATH=~/.ssh/id_rsa      # SSH key path
```

---

## Changelog

### Version 1.0.0 (2026-01-18)
- Initial CLAUDE.md creation
- Comprehensive codebase documentation
- Development workflow guidelines
- Coding conventions and patterns
- Testing strategy documentation
- Git workflow and best practices
- Common tasks and troubleshooting
- AI assistant guidelines and tips

---

## Additional Resources

- **GitHub Repository**: Main repository
- **Issue Tracker**: GitHub Issues
- **Documentation**: See /docs directory
- **Examples**: See /examples directory

---

**Document Maintainer**: Project maintainers
**Last Review**: 2026-01-18
**Next Review**: As needed when major changes occur

---

*This document is specifically designed for AI assistants working with the WIREDUP codebase. Keep it updated as the project evolves.*
