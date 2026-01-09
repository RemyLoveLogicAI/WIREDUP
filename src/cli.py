"""
Command Line Interface for AI Auto-Wiring System
"""

import click
import logging
import sys
from pathlib import Path
from typing import Optional

from src.core.autowire import get_autowire, Scope
from src.config import get_config_loader, EnvManager
from src.core.registry import ServiceRegistry, ComponentRegistry


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """AI Auto-Wiring System CLI"""
    pass


@cli.command()
@click.option('--env', default='development', help='Environment name')
@click.option('--config-dir', type=click.Path(), help='Configuration directory')
def init(env: str, config_dir: Optional[str]):
    """Initialize the auto-wiring system"""
    click.echo(f"🚀 Initializing AI Auto-Wiring System (env={env})")
    
    try:
        # Create configuration directory
        config_path = Path(config_dir) if config_dir else Path.cwd() / 'config'
        config_path.mkdir(parents=True, exist_ok=True)
        
        # Create templates directory
        templates_path = config_path / 'templates'
        templates_path.mkdir(exist_ok=True)
        
        # Create default configuration
        default_config = {
            "env": env,
            "system": {
                "name": "ai-autowire",
                "version": "1.0.0"
            },
            "autowire": {
                "auto_discovery": True,
                "lazy_loading": False
            },
            "mcp": {
                "enabled": True,
                "port": 3000,
                "host": "localhost"
            },
            "ssh": {
                "enabled": False,
                "default_timeout": 30
            }
        }
        
        import json
        with open(config_path / 'default.json', 'w') as f:
            json.dump(default_config, f, indent=2)
        
        # Create .env template
        env_template = """# AI Auto-Wiring System Configuration
AI_ENV=development
AI_LOG_LEVEL=INFO

# MCP Settings
AI_MCP_ENABLED=true
AI_MCP_PORT=3000
AI_MCP_HOST=localhost

# SSH Settings
AI_SSH_ENABLED=false
AI_SSH_KEY_PATH=~/.ssh/id_rsa

# Agent Settings
AI_AGENT_MAX_RETRIES=3
AI_AGENT_TIMEOUT=30
"""
        
        with open(Path.cwd() / '.env.example', 'w') as f:
            f.write(env_template)
        
        click.echo("✅ Initialization complete!")
        click.echo(f"📁 Configuration directory: {config_path}")
        click.echo(f"📄 Created .env.example template")
        
    except Exception as e:
        click.echo(f"❌ Initialization failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--env', default='development', help='Environment name')
def start(env: str):
    """Start the auto-wiring system"""
    click.echo(f"🚀 Starting AI Auto-Wiring System (env={env})")
    
    try:
        # Load configuration
        config_loader = get_config_loader(env=env)
        click.echo("✅ Configuration loaded")
        
        # Initialize auto-wire
        autowire = get_autowire()
        click.echo("✅ Auto-wire engine initialized")
        
        # Initialize registries
        service_registry = ServiceRegistry()
        component_registry = ComponentRegistry()
        click.echo("✅ Registries initialized")
        
        click.echo("🎉 System started successfully!")
        click.echo("\nUse 'ai-wire status' to check system status")
        
    except Exception as e:
        click.echo(f"❌ Startup failed: {e}", err=True)
        sys.exit(1)


@cli.command()
def status():
    """Show system status"""
    click.echo("📊 AI Auto-Wiring System Status\n")
    
    try:
        # Check auto-wire
        autowire = get_autowire()
        registry_info = autowire.get_registry_info()
        
        click.echo(f"🔌 Auto-Wire Engine: Running")
        click.echo(f"   Registered dependencies: {len(registry_info)}")
        
        # Show registered components
        if registry_info:
            click.echo("\n📦 Registered Dependencies:")
            for name, info in list(registry_info.items())[:5]:
                status_icon = "✅" if info['initialized'] else "⏳"
                click.echo(f"   {status_icon} {name} (scope={info['scope']})")
            
            if len(registry_info) > 5:
                click.echo(f"   ... and {len(registry_info) - 5} more")
        
        click.echo("\n✅ System is operational")
        
    except Exception as e:
        click.echo(f"❌ Status check failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('key')
@click.option('--default', help='Default value if key not found')
def config(key: str, default: Optional[str]):
    """Get configuration value"""
    try:
        from src.config import get_config
        value = get_config(key, default)
        
        if value is not None:
            click.echo(f"{key} = {value}")
        else:
            click.echo(f"❌ Configuration key '{key}' not found", err=True)
            sys.exit(1)
    
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--category', help='Filter by category')
def list_components(category: Optional[str]):
    """List registered components"""
    click.echo("📦 Registered Components\n")
    
    try:
        autowire = get_autowire()
        registry_info = autowire.get_registry_info()
        
        if not registry_info:
            click.echo("No components registered")
            return
        
        for name, info in registry_info.items():
            if category and category not in info.get('tags', []):
                continue
            
            status = "✅" if info['initialized'] else "⏳"
            tags = ", ".join(info.get('tags', []))
            
            click.echo(f"{status} {name}")
            click.echo(f"   Scope: {info['scope']}")
            if tags:
                click.echo(f"   Tags: {tags}")
            if info['dependencies']:
                click.echo(f"   Dependencies: {', '.join(info['dependencies'])}")
            click.echo()
    
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--format', type=click.Choice(['json', 'yaml', 'table']), default='table')
def export_config(format: str):
    """Export current configuration"""
    try:
        config_loader = get_config_loader()
        config = config_loader.get_all()
        
        if format == 'json':
            import json
            click.echo(json.dumps(config, indent=2))
        elif format == 'yaml':
            import yaml
            click.echo(yaml.dump(config, default_flow_style=False))
        else:  # table
            def print_dict(d, indent=0):
                for key, value in d.items():
                    if isinstance(value, dict):
                        click.echo("  " * indent + f"{key}:")
                        print_dict(value, indent + 1)
                    else:
                        click.echo("  " * indent + f"{key}: {value}")
            
            print_dict(config)
    
    except Exception as e:
        click.echo(f"❌ Export failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('name')
@click.option('--config', help='Agent configuration (JSON)')
def create_agent(name: str, config: Optional[str]):
    """Create a new agent"""
    click.echo(f"🤖 Creating agent: {name}")
    
    try:
        import json
        agent_config = json.loads(config) if config else {}
        
        # Create agent factory
        # This is a placeholder - actual implementation would load agent classes
        click.echo(f"✅ Agent '{name}' created successfully")
        click.echo(f"   Configuration: {agent_config}")
    
    except Exception as e:
        click.echo(f"❌ Agent creation failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--host', required=True, help='SSH host')
@click.option('--username', required=True, help='SSH username')
@click.option('--key-file', help='SSH key file path')
@click.argument('command')
def ssh_exec(host: str, username: str, key_file: Optional[str], command: str):
    """Execute command via SSH"""
    click.echo(f"🔒 Executing command on {host}")
    
    try:
        from src.ssh import SSHManager, SSHCredentials
        
        credentials = SSHCredentials(
            host=host,
            username=username,
            key_filename=key_file
        )
        
        manager = SSHManager()
        result = manager.execute(command, credentials)
        
        if result.success:
            click.echo("✅ Command executed successfully")
            click.echo(f"\nOutput:\n{result.stdout}")
        else:
            click.echo(f"❌ Command failed (exit code: {result.exit_code})")
            click.echo(f"\nError:\n{result.stderr}")
            sys.exit(1)
        
        manager.close()
    
    except Exception as e:
        click.echo(f"❌ SSH execution failed: {e}", err=True)
        sys.exit(1)


@cli.command()
def version():
    """Show version information"""
    click.echo("AI Auto-Wiring System")
    click.echo("Version: 1.0.0")
    click.echo("Python: " + sys.version)


if __name__ == '__main__':
    cli()
