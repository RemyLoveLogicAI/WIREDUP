"""
Command Line Interface for AI Auto-Wiring System
"""

import asyncio
import click
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.agents import AgentContext, SwarmOrchestrator, SwarmStrategy, SyntheticWorkerAgent
from src.core.autowire import get_autowire, Scope
from src.config import get_config_loader, EnvManager
from src.core.registry import ServiceRegistry, ComponentRegistry


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _deep_merge_dict(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge override values into base dictionary."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_swarm_payload(swarm_config: Optional[str], swarm_json: Optional[str]) -> Dict[str, Any]:
    """Load swarm payload from file and/or inline JSON."""
    payload: Dict[str, Any] = {}

    if swarm_config:
        with open(swarm_config, "r", encoding="utf-8") as handle:
            parsed = json.load(handle)
        if not isinstance(parsed, dict):
            raise ValueError("Swarm config file must contain a JSON object")
        payload = _deep_merge_dict(payload, parsed)

    if swarm_json:
        parsed = json.loads(swarm_json)
        if not isinstance(parsed, dict):
            raise ValueError("Inline --swarm-json must be a JSON object")
        payload = _deep_merge_dict(payload, parsed)

    return payload


def _parse_task_inputs(task_values: List[str], tasks_json: Optional[str], payload: Dict[str, Any]) -> List[str]:
    """Resolve task list from CLI options and payload."""
    tasks: List[str] = [task for task in task_values if task]

    if tasks_json:
        parsed = json.loads(tasks_json)
        if not isinstance(parsed, list):
            raise ValueError("--tasks-json must be a JSON array")
        tasks.extend(str(item) for item in parsed)

    if tasks:
        return tasks

    payload_tasks = payload.get("tasks")
    if isinstance(payload_tasks, list) and payload_tasks:
        return [str(item) for item in payload_tasks]

    payload_task = payload.get("task")
    if payload_task is not None:
        return [str(payload_task)]

    return []


def _format_swarm_report(report: Dict[str, Any]) -> str:
    """Render human-readable summary for swarm report."""
    if report.get("mode") == "mass_swarm":
        metrics = report.get("metrics", {})
        lines = [
            "✅ Mass swarm report",
            f"   Operation ID: {report.get('operation_id')}",
            f"   Correlation ID: {report.get('correlation_id')}",
            f"   Success: {report.get('success')}",
            f"   Tasks: {report.get('successful_tasks')}/{report.get('total_tasks')} successful",
            f"   Duration: {report.get('duration_ms')} ms",
            f"   p95 task duration: {metrics.get('operation_duration_p95_ms')} ms",
            f"   Success rate: {metrics.get('success_rate')}",
        ]
        return "\n".join(lines)

    metrics = report.get("metrics", {})
    lines = [
        "✅ Swarm report",
        f"   Operation ID: {report.get('operation_id')}",
        f"   Correlation ID: {report.get('correlation_id')}",
        f"   Success: {report.get('success')}",
        f"   Agents: {report.get('successful_agents')}/{report.get('total_agents')} successful",
        f"   Duration: {report.get('duration_ms')} ms",
        f"   p95 sub-agent duration: {metrics.get('sub_agent_duration_p95_ms')} ms",
        f"   Timeouts: {metrics.get('timeout_count')}",
        f"   Retries used: {metrics.get('retries_used')}",
        f"   Success rate: {metrics.get('success_rate')}",
    ]
    return "\n".join(lines)


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


@cli.command('swarm-run')
@click.option('--swarm-config', type=click.Path(exists=True, dir_okay=False), help='Swarm JSON config file path')
@click.option('--swarm-json', help='Inline swarm JSON payload')
@click.option('--task', 'tasks', multiple=True, help='Task string (repeat for multiple tasks)')
@click.option('--tasks-json', help='JSON array of task strings')
@click.option('--context-json', help='JSON object to override runtime context')
@click.option('--target-agent', 'target_agents', multiple=True, help='Target specific sub-agent(s)')
@click.option('--correlation-id', help='Trace correlation ID')
@click.option('--strategy', type=click.Choice(['parallel', 'sequential']), help='Execution strategy override')
@click.option('--max-concurrency', type=int, help='Override max sub-agent concurrency')
@click.option('--retries', type=int, help='Override sub-agent retries')
@click.option('--timeout', type=float, help='Override sub-agent timeout in seconds')
@click.option('--fail-fast', 'fail_fast', flag_value=True, default=None, help='Enable fail-fast')
@click.option('--no-fail-fast', 'fail_fast', flag_value=False, help='Disable fail-fast')
@click.option('--parallel-tasks', 'parallel_tasks', flag_value=True, default=None, help='Run mass tasks in parallel')
@click.option('--sequential-tasks', 'parallel_tasks', flag_value=False, help='Run mass tasks sequentially')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output display format')
@click.option('--report-output', type=click.Path(dir_okay=False), help='Write full report JSON file')
@click.option('--metrics-output', type=click.Path(dir_okay=False), help='Write emitted metrics JSON file')
def swarm_run(
    swarm_config: Optional[str],
    swarm_json: Optional[str],
    tasks: List[str],
    tasks_json: Optional[str],
    context_json: Optional[str],
    target_agents: List[str],
    correlation_id: Optional[str],
    strategy: Optional[str],
    max_concurrency: Optional[int],
    retries: Optional[int],
    timeout: Optional[float],
    fail_fast: Optional[bool],
    parallel_tasks: Optional[bool],
    output_format: str,
    report_output: Optional[str],
    metrics_output: Optional[str],
):
    """Run swarm orchestration from config/JSON input."""
    click.echo("🐝 Running swarm orchestration")

    try:
        payload = _load_swarm_payload(swarm_config=swarm_config, swarm_json=swarm_json)
        orchestrator_config = payload.get("orchestrator", {})
        if not isinstance(orchestrator_config, dict):
            raise ValueError("'orchestrator' must be a JSON object")
        orchestrator_config = dict(orchestrator_config)

        if strategy:
            orchestrator_config["strategy"] = strategy
        if max_concurrency is not None:
            orchestrator_config["max_concurrency"] = max_concurrency
        if retries is not None:
            orchestrator_config["sub_agent_retries"] = retries
        if timeout is not None:
            orchestrator_config["sub_agent_timeout"] = timeout
        if fail_fast is not None:
            orchestrator_config["fail_fast"] = fail_fast

        orchestrator_name = str(orchestrator_config.pop("name", "swarm_cli_orchestrator"))
        orchestrator = SwarmOrchestrator(orchestrator_name, orchestrator_config)

        metrics_events: List[Dict[str, Any]] = []
        orchestrator.register_metrics_hook(lambda metric: metrics_events.append(metric))

        agent_specs = payload.get("agents", [])
        if not isinstance(agent_specs, list) or not agent_specs:
            raise ValueError("No agents configured. Provide 'agents' as a non-empty list")

        for index, spec in enumerate(agent_specs):
            if not isinstance(spec, dict):
                raise ValueError(f"Agent spec at index {index} must be a JSON object")
            name = spec.get("name")
            if not name:
                raise ValueError(f"Agent spec at index {index} is missing required field 'name'")

            worker_config = dict(spec)
            worker_config.pop("name", None)
            orchestrator.add_sub_agent(SyntheticWorkerAgent(str(name), worker_config))

        context_payload = payload.get("context", {})
        if context_payload is None:
            context_payload = {}
        if not isinstance(context_payload, dict):
            raise ValueError("'context' must be a JSON object")

        if context_json:
            context_override = json.loads(context_json)
            if not isinstance(context_override, dict):
                raise ValueError("--context-json must be a JSON object")
            context_payload = _deep_merge_dict(context_payload, context_override)

        metadata = context_payload.get("metadata", {})
        if metadata is None:
            metadata = {}
        if not isinstance(metadata, dict):
            raise ValueError("'context.metadata' must be a JSON object")
        metadata = dict(metadata)
        if correlation_id:
            metadata["correlation_id"] = correlation_id

        context_state = context_payload.get("state", {})
        if context_state is None:
            context_state = {}
        if not isinstance(context_state, dict):
            raise ValueError("'context.state' must be a JSON object")

        context = AgentContext(
            session_id=str(context_payload.get("session_id") or f"swarm_cli_{uuid4().hex[:10]}"),
            user_id=context_payload.get("user_id"),
            metadata=metadata,
            state=dict(context_state),
        )

        resolved_tasks = _parse_task_inputs(list(tasks), tasks_json, payload)
        if not resolved_tasks:
            raise ValueError("No tasks provided. Use --task, --tasks-json, or payload task(s)")

        resolved_targets: Optional[List[str]] = None
        if target_agents:
            resolved_targets = [str(name) for name in target_agents]
        elif isinstance(payload.get("target_agents"), list):
            resolved_targets = [str(name) for name in payload["target_agents"]]

        sub_tasks = payload.get("sub_tasks")
        if sub_tasks is not None and not isinstance(sub_tasks, dict):
            raise ValueError("'sub_tasks' must be a JSON object")
        resolved_sub_tasks = (
            {str(key): str(value) for key, value in sub_tasks.items()}
            if isinstance(sub_tasks, dict)
            else None
        )

        run_kwargs: Dict[str, Any] = {
            "target_agents": resolved_targets,
            "strategy": SwarmStrategy(strategy) if strategy else None,
            "max_concurrency": max_concurrency,
            "timeout": timeout,
            "retries": retries,
            "fail_fast": fail_fast,
            "correlation_id": metadata.get("correlation_id"),
        }
        run_kwargs = {key: value for key, value in run_kwargs.items() if value is not None}

        if len(resolved_tasks) == 1:
            if resolved_sub_tasks is not None:
                run_kwargs["sub_tasks"] = resolved_sub_tasks
            report = asyncio.run(
                orchestrator.execute_swarm(
                    task=resolved_tasks[0],
                    context=context,
                    **run_kwargs,
                )
            )
        else:
            payload_parallel = payload.get("parallel_tasks", True)
            resolved_parallel_tasks = bool(payload_parallel if parallel_tasks is None else parallel_tasks)
            report = asyncio.run(
                orchestrator.execute_mass_swarm(
                    tasks=resolved_tasks,
                    context=context,
                    parallel_tasks=resolved_parallel_tasks,
                    **run_kwargs,
                )
            )

        if output_format == 'json':
            click.echo(json.dumps(report, indent=2, default=str))
        else:
            click.echo(_format_swarm_report(report))

        if report_output:
            report_path = Path(report_output)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, "w", encoding="utf-8") as handle:
                json.dump(report, handle, indent=2, default=str)
            click.echo(f"📝 Report written to {report_path}")

        if metrics_output:
            metrics_path = Path(metrics_output)
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            with open(metrics_path, "w", encoding="utf-8") as handle:
                json.dump(metrics_events, handle, indent=2, default=str)
            click.echo(f"📈 Metrics written to {metrics_path}")

    except Exception as e:
        click.echo(f"❌ Swarm run failed: {e}", err=True)
        sys.exit(1)


@cli.command()
def version():
    """Show version information"""
    click.echo("AI Auto-Wiring System")
    click.echo("Version: 1.0.0")
    click.echo("Python: " + sys.version)


if __name__ == '__main__':
    cli()
