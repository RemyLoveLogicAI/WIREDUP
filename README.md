# 🚀 AI Auto-Wiring System

> Revolutionary Environment, MCP, SSH, and Agent Configuration System with Automatic Dependency Injection

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 🌟 Features

- **🔌 Auto-Wiring Engine**: Intelligent dependency injection for AI agents
- **🌍 ENV Management**: Sophisticated environment configuration with validation
- **🤖 MCP Integration**: Model Context Protocol for advanced AI communication
- **🔒 SSH Security**: Secure connection management with key rotation
- **📊 Agent Orchestration**: Multi-agent coordination and communication
- **⚙️ Config Auto-Discovery**: Smart configuration loading from multiple sources
- **🎯 Skills Registry**: Dynamic capability management and discovery
- **📝 Comprehensive Docs**: AGENT.md and SKILLS.md with best practices

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Auto-Wiring Core                     │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐       │
│  │   ENV     │  │    MCP    │  │    SSH    │       │
│  │  Manager  │  │  Protocol │  │  Manager  │       │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘       │
│        │              │              │               │
│        └──────────────┴──────────────┘               │
│                       │                              │
│              ┌────────▼────────┐                     │
│              │  Config Loader  │                     │
│              └────────┬────────┘                     │
│                       │                              │
│         ┌─────────────┴─────────────┐               │
│         │                           │               │
│    ┌────▼────┐              ┌──────▼──────┐        │
│    │  Agent  │◄────────────►│   Skills    │        │
│    │Registry │              │   Registry  │        │
│    └─────────┘              └─────────────┘        │
└─────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd ai-auto-wiring

# Install dependencies
pip install -r requirements.txt

# Initialize the system
python -m src.cli init

# Start the auto-wiring system
python -m src.cli start
```

### Basic Usage

```python
from src.core.autowire import AutoWire
from src.agents.base_agent import BaseAgent

# Initialize auto-wiring system
wire = AutoWire()

# Auto-discover and load configurations
wire.discover_configs()

# Create and wire agents
agent = wire.create_agent('research_agent', {
    'model': 'gpt-4',
    'max_tokens': 4096
})

# Execute with automatic dependency injection
result = agent.execute("Analyze quantum computing trends")
```

## 📚 Documentation

- [AGENT.md](./AGENT.md) - Comprehensive agent development guide
- [SKILLS.md](./SKILLS.md) - Skills registry and capabilities matrix
- [CONFIG.md](./docs/CONFIG.md) - Configuration system documentation
- [MCP.md](./docs/MCP.md) - Model Context Protocol integration
- [SSH.md](./docs/SSH.md) - SSH management and security

## 🎯 Core Components

### 1. Auto-Wiring Engine
Intelligent dependency injection that automatically resolves and injects dependencies for agents, services, and configurations.

### 2. ENV Management
Multi-environment support with validation, encryption, and dynamic reloading.

### 3. MCP Protocol
Full Model Context Protocol implementation for standardized AI communication.

### 4. SSH Management
Secure connection pooling, key rotation, and credential management.

### 5. Agent System
Extensible agent framework with automatic capability discovery.

## 🔧 Configuration

Create a `.env` file or use environment variables:

```env
# Core Configuration
AI_ENV=development
AI_LOG_LEVEL=INFO

# MCP Settings
MCP_ENABLED=true
MCP_PORT=3000
MCP_HOST=localhost

# SSH Configuration
SSH_KEY_PATH=~/.ssh/id_rsa
SSH_KNOWN_HOSTS=~/.ssh/known_hosts

# Agent Settings
AGENT_MAX_RETRIES=3
AGENT_TIMEOUT=30
```

## 🧪 Examples

See the [examples](./examples) directory for complete examples:

- `basic_agent.py` - Simple agent creation
- `multi_agent.py` - Multi-agent orchestration
- `mcp_integration.py` - MCP protocol usage
- `ssh_deployment.py` - Remote deployment via SSH

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

Built with modern Python best practices and inspired by enterprise-grade dependency injection frameworks.

---

**Made with ❤️ for the AI development community**
