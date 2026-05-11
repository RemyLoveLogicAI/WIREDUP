# Release Notes

## 2026-02-19 - Swarm Orchestration + CLI Operations

### Highlights

- Added production swarm orchestration engine:
  - `SwarmOrchestrator.execute_swarm(...)`
  - `SwarmOrchestrator.execute_mass_swarm(...)`
- Added real operations CLI:
  - `ai-wire swarm-run`
- Added observability hooks:
  - Structured operation logs
  - Metrics hooks with per-operation payloads
  - Operation and correlation IDs for traceability

### New Orchestrator API

- `execute_swarm(task, context, ...)`
  - Fan-out a single task across sub-agents
  - Supports targeted routing and per-agent task overrides
- `execute_mass_swarm(tasks, context, ...)`
  - Runs batches of swarm operations
  - Supports parallel or sequential task dispatch

### Observability Metrics

Each operation now emits metrics including:

- success/failure rate
- p95 duration (`sub_agent_duration_p95_ms` or `operation_duration_p95_ms`)
- timeout count
- retries used
- operation ID and correlation ID

### CLI: `swarm-run`

Run swarm jobs from JSON file or inline JSON:

```bash
ai-wire swarm-run --swarm-config config/swarm.json --output-format json
```

Useful options:

- `--max-concurrency`
- `--retries`
- `--timeout`
- `--fail-fast` / `--no-fail-fast`
- `--report-output`
- `--metrics-output`
