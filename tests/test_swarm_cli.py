"""
CLI tests for swarm-run command.
"""

import json

from click.testing import CliRunner

from src.cli import cli


def _extract_json_from_output(output: str):
    start = output.find("{")
    if start < 0:
        raise AssertionError(f"No JSON payload found in output:\n{output}")
    return json.loads(output[start:])


def test_swarm_run_inline_json_single_operation():
    runner = CliRunner()
    payload = {
        "orchestrator": {
            "name": "cli_orchestrator",
            "strategy": "parallel",
            "max_concurrency": 2,
            "sub_agent_timeout": 1,
            "metrics_logging": False,
        },
        "agents": [
            {"name": "w1", "delay_ms": 1},
            {"name": "w2", "delay_ms": 1},
        ],
        "task": "inline-task",
        "context": {"session_id": "cli-inline-session"},
    }

    result = runner.invoke(
        cli,
        ["swarm-run", "--swarm-json", json.dumps(payload), "--output-format", "json"],
    )

    assert result.exit_code == 0
    report = _extract_json_from_output(result.output)
    assert report["success"] is True
    assert report["total_agents"] == 2
    assert report["successful_agents"] == 2
    assert report["metrics"]["event"] == "swarm_operation"
    assert report["operation_id"].startswith("swarm_")


def test_swarm_run_config_mass_mode_with_report_and_metrics_files(tmp_path):
    runner = CliRunner()
    config_path = tmp_path / "swarm.json"
    report_path = tmp_path / "report.json"
    metrics_path = tmp_path / "metrics.json"

    payload = {
        "orchestrator": {
            "name": "cli_mass_orchestrator",
            "strategy": "parallel",
            "max_concurrency": 3,
            "sub_agent_retries": 1,
            "sub_agent_timeout": 1,
            "metrics_logging": False,
        },
        "agents": [
            {"name": "worker_ok", "delay_ms": 1},
            {"name": "worker_flaky", "failure_mode": "first_attempt", "delay_ms": 1},
        ],
        "tasks": ["mass-task-1", "mass-task-2"],
        "parallel_tasks": True,
        "context": {"session_id": "cli-mass-session"},
    }
    config_path.write_text(json.dumps(payload), encoding="utf-8")

    result = runner.invoke(
        cli,
        [
            "swarm-run",
            "--swarm-config",
            str(config_path),
            "--output-format",
            "json",
            "--report-output",
            str(report_path),
            "--metrics-output",
            str(metrics_path),
            "--correlation-id",
            "corr-cli-123",
        ],
    )

    assert result.exit_code == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    assert report["mode"] == "mass_swarm"
    assert report["success"] is True
    assert report["total_tasks"] == 2
    assert report["successful_tasks"] == 2
    assert report["failed_tasks"] == 0
    assert report["correlation_id"] == "corr-cli-123"
    assert report["metrics"]["event"] == "mass_swarm_operation"
    assert len(metrics) >= 3  # two swarm ops + one mass op
    assert any(metric["event"] == "mass_swarm_operation" for metric in metrics)
