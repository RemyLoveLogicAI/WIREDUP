<details>
<summary>Documentation Metadata (click to expand)</summary>

```json
{
  "doc_type": "file_overview",
  "file_path": "src/agents/swarm_orchestrator.py",
  "source_hash": "63c319efdb3df9d329f8cae9b2ce07810c128796e69f2840bfb556ab71712711",
  "last_updated": "2026-02-19T18:57:09.387862+00:00",
  "tokens_used": 64332,
  "complexity_score": 6,
  "estimated_review_time_minutes": 25,
  "external_dependencies": []
}
```

</details>

[Documentation Home](../../README.md) > [src](../README.md) > [agents](./README.md) > **swarm_orchestrator**

---

# swarm_orchestrator.py

> **File:** `src/agents/swarm_orchestrator.py`

![Complexity: Medium](https://img.shields.io/badge/Complexity-Medium-yellow) ![Review Time: 25min](https://img.shields.io/badge/Review_Time-25min-blue)

## 📑 Table of Contents


- [Overview](#overview)
- [Dependencies](#dependencies)
- [Architecture Notes](#architecture-notes)
- [Usage Examples](#usage-examples)
- [Maintenance Notes](#maintenance-notes)
- [Functions and Classes](#functions-and-classes)

---

## Overview

This file defines a SwarmOrchestrator class that inherits from BaseAgent and is responsible for executing a given task across a set of registered sub-agents. It implements two execution strategies (parallel and sequential) via the SwarmStrategy enum and exposes high-level operations: execute_swarm (run one orchestrated operation across agents) and execute_mass_swarm (run a batch of swarm operations). The orchestrator supports configuration for max_concurrency, per-sub-agent timeout (_sub_agent_timeout), retries (_sub_agent_retries), fail_fast semantics (_fail_fast), context isolation (_isolate_context), and a limit on concurrent mass tasks (_max_task_concurrency). The SubAgentResult dataclass captures per-agent execution metadata (agent name, success boolean, output, error message, attempts, timed_out flag, and measured duration in ms) and exposes to_dict() using dataclasses.asdict for serialization.

SwarmOrchestrator implements specific concurrency and error-handling patterns: sequential execution runs agents one-by-one and can short-circuit remaining agents with a "fail_fast" policy; parallel execution creates asyncio tasks per agent and limits concurrent running tasks using an asyncio.Semaphore set to max_concurrency, and it cancels outstanding tasks when fail_fast triggers. Per-agent execution is performed in _execute_single_agent which creates a sub-context (via _create_sub_context that optionally deep-copies parent.state), invokes the agent.execute coroutine, handles asyncio.TimeoutError (respecting a per-attempt timeout), retries failed attempts up to the configured retries count, and returns a SubAgentResult for each agent. Reporting is built by _build_report which aggregates result counts, timestamps, durations, and a summary string; execute_swarm also records a brief entry into context.state["swarm_history"]. The class logs lifecycle events (adding agents, warnings on failures/timeouts) via the module logger.

## Dependencies

### Internal Dependencies

| Module | Usage |
| --- | --- |
| `asyncio` | Used extensively for asynchronous orchestration: asyncio.Semaphore for concurrency limits (in _run_parallel and execute_mass_swarm), asyncio.create_task to schedule per-agent tasks, asyncio.as_completed to iterate finished tasks, asyncio.wait_for to apply per-attempt timeouts in _execute_single_agent, asyncio.gather to wait for and collect task results, and asyncio.TimeoutError for timeout handling. |
| `copy` | copy.deepcopy is used inside _create_sub_context to create an isolated deep copy of parent.state when _isolate_context is True, preventing shared-state races between concurrently running sub-agents. |
| `logging` | Module-level logger = logging.getLogger(__name__) is used for informational logging (self.log_info via BaseAgent) and explicit calls to self.log_warning within _execute_single_agent when a sub-agent times out or raises an exception. |
| `dataclasses` | from dataclasses import asdict, dataclass. @dataclass decorates SubAgentResult to auto-generate initializer and other methods; asdict is used in SubAgentResult.to_dict() to produce a serializable dictionary representation of the dataclass. |
| `datetime` | from datetime import datetime, timezone. datetime.now(timezone.utc).isoformat() is used to create ISO-8601 UTC timestamps for started_at and finished_at fields in reports (execute_swarm, execute_mass_swarm, _build_report). |
| `enum` | from enum import Enum. Defines SwarmStrategy(Enum) with values 'parallel' and 'sequential' to control execution strategy; _resolve_strategy accepts either the enum or strings and maps them into SwarmStrategy. |
| `time` | from time import perf_counter. perf_counter() is used to measure high-resolution durations for per-agent execution and overall operation durations, with results converted to milliseconds (duration_ms fields). |
| `typing` | from typing import Any, Dict, List, Optional, Sequence. Provides type hints for signatures throughout the file (e.g., execute_swarm, execute_mass_swarm, _run_parallel), improving readability and static analysis. |
| [.base_agent](..//base_agent.md) | from .base_agent import AgentContext, BaseAgent. BaseAgent is the parent class of SwarmOrchestrator (class SwarmOrchestrator(BaseAgent)), and AgentContext is used as the typed context passed into execute_swarm/execute_mass_swarm and used to create isolated sub-contexts for sub-agents in _create_sub_context. |

## 📁 Directory

This file is part of the **agents** directory. View the [directory index](_docs/src/agents/README.md) to see all files in this module.

## Architecture Notes

- Asynchronous orchestration: The implementation leverages asyncio (async/await) throughout to avoid blocking; per-agent work uses coroutines returned by agent.execute and concurrency is controlled via asyncio.Semaphore and task scheduling (asyncio.create_task, asyncio.as_completed).
- Concurrency control and fail-fast semantics: Parallel execution uses a semaphore to limit concurrent executions to max_concurrency. If fail_fast is set and a sub-agent fails, remaining pending tasks are cancelled and replaced with SubAgentResult entries indicating cancellation or skipping; sequential execution can short-circuit remaining agents when fail_fast is enabled.
- Context isolation: By default _isolate_context is True and _create_sub_context deep-copies parent.state when creating AgentContext for each sub-agent, preventing shared-state races between concurrently executing sub-agents. This is a deliberate trade-off (safety vs memory/copy cost).
- Error handling and retries: _execute_single_agent attempts execution up to (retries + 1) times, catches asyncio.TimeoutError to set timed_out and logs a warning, catches other Exceptions as failures (logged) and returns a SubAgentResult with attempts, last error, and duration. execute_swarm aggregates per-agent results into a report and also appends a summary entry into context.state['swarm_history'].

## Usage Examples

### Run a single swarm operation targeting all registered sub-agents in parallel with defaults

Call await orchestrator.execute_swarm(task='do work', context=ctx). The orchestrator will use its configured strategy (default PARALLEL), max_concurrency, per-agent timeout and retries. For each sub-agent, _create_sub_context builds an isolated AgentContext (deep-copy of parent.state by default), then _execute_single_agent calls the sub-agent's execute coroutine and awaits the result (with asyncio.wait_for when timeout is set). The function returns a report dict containing success boolean, per-agent SubAgentResult entries (serialized via to_dict()), counts (total_agents, successful_agents, failed_agents), timestamps and duration_ms.

### Execute many tasks (mass mode) with limited parallelism for tasks

Call await orchestrator.execute_mass_swarm(tasks=list_of_task_strings, context=ctx, parallel_tasks=True). The orchestrator will schedule up to _max_task_concurrency tasks in parallel (using an asyncio.Semaphore) and for each task call execute_swarm internally. The returned mass report includes operations (each operation is a swarm report), total_tasks, successful_tasks, failed_tasks and aggregated duration. This pattern is useful for bulk operations where each task targets the same set of sub-agents.

### Run a sequential swarm with fail-fast

Call await orchestrator.execute_swarm(task='job', context=ctx, strategy=SwarmStrategy.SEQUENTIAL, fail_fast=True). The orchestrator will call sub-agents in order; on the first failing SubAgentResult it will stop executing further agents and append SubAgentResult entries for skipped agents with error 'Skipped due to fail_fast policy'. The returned report will reflect fewer executed agents and indicate overall failure.

## Maintenance Notes

- Performance considerations: _isolate_context defaults to True and uses copy.deepcopy on parent.state per sub-agent; if parent.state is large this can become a memory and CPU bottleneck. Consider toggling isolate_context to False when sub-agents are trusted or reducing the size of parent.state.
- Cancellation and cleanup: When fail_fast cancels pending asyncio.Tasks in _run_parallel, tasks are cancelled and asyncio.gather(..., return_exceptions=True) is used to suppress propagate cancellations. Ensure sub-agents' execute coroutines handle asyncio.CancelledError if they perform cleanup or external I/O.
- Testing edge cases: Unit tests should cover timeouts (asyncio.TimeoutError path), multiple retries, fail_fast behavior (both sequential and parallel), and context isolation behavior (mutations to state should not leak between sub-agents when isolate_context=True). Tests should also validate that unknown agent names passed to execute_swarm raise ValueError.
- Future enhancements: Add per-agent custom timeouts/retries via sub_tasks metadata, richer error types (structured error codes), backoff strategy for retries, and better instrumentation (metrics exported for durations, timeouts, cancellations).
- Dependency management: All imports are standard library or internal (.base_agent); keep an eye on the internal BaseAgent/AgentContext API compatibility if their signatures or attributes change (e.g., metadata/state shapes).

---

## Navigation

**↑ Parent Directory:** [Go up](_docs/src/agents/README.md)

---

*This documentation was automatically generated by AI ([Woden DocBot](https://github.com/marketplace/ai-document-creator)) and may contain errors. It is the responsibility of the user to validate the accuracy and completeness of this documentation.*


---

## Functions and Classes


#### to_dict

![Type: Sync](https://img.shields.io/badge/Type-Sync-green)

### Signature

```python
def to_dict(self) -> Dict[str, Any]
```

### Description

Return a serializable dictionary representation of the object by delegating to asdict(self).


This method calls the asdict function and returns its result. The implementation contains a single return statement: return asdict(self). There is no other logic, branching, or mutation in the body. The returned value is whatever asdict(self) produces for the provided self object.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `self` | `self` | ✅ | The instance on which the method is called; passed directly to asdict.
<br>**Constraints:** No constraints enforced in this method itself; behavior depends on asdict(self). |

### Returns

**Type:** `Dict[str, Any]`

The exact value returned by calling asdict(self) — a mapping produced by asdict for the given object.


**Possible Values:**

- A dictionary mapping attribute names to their values as produced by dataclasses.asdict
- Any value that dataclasses.asdict may return for the provided object

### Usage Examples

#### Convert the instance to a dictionary for serialization or inspection

```python
result = instance.to_dict()
```

Demonstrates calling the method; the method immediately returns asdict(self) with no additional processing.

### Complexity

Time complexity: O(n) where n is the number of fields processed by asdict; Space complexity: O(n) for the returned dictionary (dependent on asdict's behavior).

### Related Functions

- `dataclasses.asdict` - Called by this method; this method is a thin wrapper around dataclasses.asdict(self).

### Notes

- The method implementation is a single delegation to asdict(self). Any behavior, constraints, or exceptions stem from dataclasses.asdict rather than this method's code.
- No validation, copying, or transformation is performed beyond what asdict does.

---



#### __init__

![Type: Sync](https://img.shields.io/badge/Type-Sync-green)

### Signature

```python
def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None
```

### Description

Initializes an instance by calling the parent initializer and configuring several internal orchestration-related attributes based on provided configuration values.


This constructor calls the superclass __init__ with the provided name and config, creates an empty dictionary to hold sub-agent instances, and initializes multiple internal configuration attributes by reading values from the instance configuration (via get_config) and coercing them with helper methods. Specifically, it resolves a strategy, computes integer-based limits with bounds, coerces a timeout and boolean flags, and sets defaults for missing configuration entries.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | `str` | ✅ | Identifier/name passed to the parent initializer; likely used to identify this orchestrator instance.
 |
| `config` = `None` | `Optional[Dict[str, Any]]` | ❌ | Optional configuration dictionary used by get_config to obtain configuration values for initializing attributes.
 |

### Returns

**Type:** `None`

Constructors do not return a value; the method returns None implicitly.


**Possible Values:**

- None

### Side Effects

> ❗ **IMPORTANT**
> This function has side effects that modify state or perform I/O operations.

- Calls super().__init__(name, config) which may have side effects defined in the superclass.
- Creates/modifies instance attributes: _sub_agents, _strategy, _max_concurrency, _sub_agent_timeout, _sub_agent_retries, _fail_fast, _isolate_context, _max_task_concurrency.

### Usage Examples

#### Create a swarm orchestrator with default configuration

```python
orchestrator = SwarmOrchestrator('orchestrator_name')
```

Initializes the orchestrator, setting defaults: strategy resolved from default, max_concurrency=8 (coerced and bounded), sub_agent_timeout=30, sub_agent_retries=0, fail_fast=False, isolate_context=True, max_task_concurrency=4.

#### Create with overridden configuration

```python
orchestrator = SwarmOrchestrator('orch', {'max_concurrency': 2, 'fail_fast': True})
```

Initializes the orchestrator using provided config values; max_concurrency will be coerced to at least 1 and fail_fast coerced to boolean True.

### Complexity

O(1) time and O(1) additional space: the method performs a fixed number of attribute assignments and helper calls regardless of input size.

### Related Functions

- `_resolve_strategy` - Called by this constructor to obtain the resolved strategy from a configuration value.
- `get_config` - Called by this constructor to read configuration values; provided by this class or a superclass.
- `_coerce_int` - Called to coerce configuration values to integers and apply defaults.
- `_coerce_timeout` - Called to coerce the sub-agent timeout configuration value.
- `_coerce_bool` - Called to coerce boolean configuration flags (fail_fast, isolate_context).

### Notes

- No explicit validation errors or exceptions are raised in this method; coercion and bounds are applied via helper methods.
- Default values are taken from get_config calls: strategy defaults to SwarmStrategy.PARALLEL.value, max_concurrency defaults to 8, sub_agent_timeout defaults to 30, sub_agent_retries defaults to 0, fail_fast defaults to False, isolate_context defaults to True, and max_task_concurrency defaults to 4.
- max_concurrency, _sub_agent_retries, and _max_task_concurrency are constrained to non-negative lower bounds via max(...).

---



#### add_sub_agent

![Type: Sync](https://img.shields.io/badge/Type-Sync-green)

### Signature

```python
def add_sub_agent(self, agent: BaseAgent) -> None
```

### Description

Register a sub-agent by storing it in the orchestrator's _sub_agents dict and log the addition; reject registration if the agent has the same name as the orchestrator.


This method accepts an object typed as BaseAgent, checks whether its name equals the orchestrator's own name and raises a ValueError if so. If the check passes, it inserts the agent into the instance's _sub_agents mapping keyed by agent.name and then calls self.log_info to record that the sub-agent was added. The method does not return a value.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `agent` | `BaseAgent` | ✅ | The sub-agent instance to register; its name attribute is used as the key in the orchestrator's _sub_agents dictionary.
<br>**Constraints:** agent must have a name attribute, agent.name must not equal self.name (the orchestrator's name) |

### Returns

**Type:** `None`

This function does not return a value; it performs registration as a side effect.


**Possible Values:**

- None

### Raises

| Exception | Condition |
| --- | --- |
| `ValueError` | Raised when agent.name == self.name to prevent the orchestrator from registering itself as a sub-agent. |

### Side Effects

> ❗ **IMPORTANT**
> This function has side effects that modify state or perform I/O operations.

- Modifies instance state: sets self._sub_agents[agent.name] = agent
- Performs logging via self.log_info(...)

### Usage Examples

#### Registering a newly created sub-agent with an orchestrator

```python
orchestrator.add_sub_agent(agent)
```

Adds the provided agent to the orchestrator's _sub_agents dict keyed by agent.name and logs the addition; will raise ValueError if agent.name matches orchestrator's name.

### Complexity

Time complexity: O(1) for the dictionary assignment and comparisons. Space complexity: O(1) additional space beyond storing the reference in self._sub_agents (the dictionary grows by one entry).

### Related Functions

- `log_info` - Called by this method to record a log entry when a sub-agent is added

### Notes

- The method assumes self._sub_agents is a mutable mapping (e.g., dict) already initialized on the instance.
- The method assumes the agent provided exposes a name attribute.
- No validation is performed beyond the self-registration check; duplicate agent.name will overwrite any existing entry in self._sub_agents.

---



#### add_sub_agents

![Type: Sync](https://img.shields.io/badge/Type-Sync-green)

### Signature

```python
def add_sub_agents(self, agents: Sequence[BaseAgent]) -> None
```

### Description

Iterate over the provided sequence and call self.add_sub_agent(agent) for each agent in the sequence.


This method accepts a sequence of BaseAgent instances (or objects typed as BaseAgent) and, for each element in that sequence, invokes the instance method add_sub_agent on self with the element as the argument. The method itself does not perform any additional logic, validation, or return a value; it simply forwards each agent to the single-agent registration method add_sub_agent.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `agents` | `Sequence[BaseAgent]` | ✅ | A sequence (e.g., list, tuple) of BaseAgent instances to be registered via self.add_sub_agent.
<br>**Constraints:** Must be an iterable/sequence containing elements compatible with self.add_sub_agent, No validation is performed by this method itself |

### Returns

**Type:** `None`

This function does not return a value; it returns None implicitly.


**Possible Values:**

- None

### Side Effects

> ❗ **IMPORTANT**
> This function has side effects that modify state or perform I/O operations.

- Calls self.add_sub_agent(agent) for each agent in the provided sequence (invokes that method's side effects, if any)

### Usage Examples

#### Register multiple sub-agents from a list

```python
orchestrator.add_sub_agents([agent1, agent2, agent3])
```

Demonstrates passing a list of BaseAgent instances; the method forwards each element to self.add_sub_agent.

### Complexity

Time: O(n) where n is the number of agents in the sequence (one call to add_sub_agent per agent). Space: O(1) additional space (only loop iteration overhead).

### Related Functions

- `add_sub_agent` - Called by this method for each element of the agents sequence; performs the per-agent registration logic.

### Notes

- This method does no validation or error handling itself; any exceptions or side effects stem from self.add_sub_agent.
- If agents is a lazy iterable (not a Sequence), the declared type Sequence[...] suggests a concrete sequence is expected, but the implementation only requires it to be iterable.

---



#### remove_sub_agent

![Type: Sync](https://img.shields.io/badge/Type-Sync-green)

### Signature

```python
def remove_sub_agent(self, agent_name: str) -> bool
```

### Description

Check whether agent_name is present in self._sub_agents, remove that entry if present, and return whether it existed prior to removal.


The method tests membership of the provided agent_name in the instance attribute dictionary self._sub_agents. It records whether the key was present, then calls dict.pop(agent_name, None) to remove the key if it exists (providing None as a default to avoid KeyError). Finally it returns a boolean indicating whether the agent_name was found before removal.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `agent_name` | `str` | ✅ | The key/name of the sub-agent to remove from the instance's _sub_agents mapping.
<br>**Constraints:** Value is used as a dictionary key; it should be a valid dictionary key (hashable) in Python. |

### Returns

**Type:** `bool`

True if agent_name was present in self._sub_agents prior to removal, False otherwise.


**Possible Values:**

- True — the key was present and has been removed
- False — the key was not present (no change to mapping)

### Side Effects

> ❗ **IMPORTANT**
> This function has side effects that modify state or perform I/O operations.

- Mutates the instance attribute self._sub_agents by removing the mapping for agent_name if it exists.

### Usage Examples

#### Remove an existing sub-agent by name and check if removal occurred

```python
removed = orchestrator.remove_sub_agent('worker-1')
```

If 'worker-1' was a key in orchestrator._sub_agents, it is removed and removed will be True; otherwise removed will be False.

#### Attempt to remove a non-existent sub-agent

```python
removed = orchestrator.remove_sub_agent('nonexistent')
```

Since 'nonexistent' is not present, the method does not raise an error and returns False.

### Complexity

Average-case time complexity O(1) for membership check and pop on a dict; worst-case dictionary pathologies aside. Space complexity O(1) additional auxiliary space.

### Notes

- The method uses dict.pop with a default value to avoid raising KeyError when the key is absent.
- The return value reflects membership prior to modification, not whether a deletion operation raised an error.

---



#### list_sub_agents

![Type: Sync](https://img.shields.io/badge/Type-Sync-green)

### Signature

```python
def list_sub_agents(self) -> List[str]
```

### Description

Return a list of the registered sub-agent names by converting the keys() view of self._sub_agents into a list.


This method accesses the instance attribute self._sub_agents, calls its keys() method to obtain a view of the dictionary keys, and returns a new list containing those keys. The returned list is a shallow list of the dictionary keys (strings) at the moment of the call. The implementation performs no iteration logic itself beyond what list(...) does and does not modify self._sub_agents.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `self` | `swarm_orchestrator instance` | ✅ | The instance of the class that owns this method; used to access the _sub_agents attribute.
<br>**Constraints:** self must have an attribute named _sub_agents that supports .keys() (typically a dict) |

### Returns

**Type:** `List[str]`

A new list containing the keys of the self._sub_agents mapping (each key expected to be a string representing a sub-agent name).


**Possible Values:**

- A list of zero or more strings (e.g., [])
- A list containing the current keys of self._sub_agents in insertion order if _sub_agents is a dict

### Usage Examples

#### Retrieve all registered sub-agent names to display or iterate over them.

```python
names = orchestrator.list_sub_agents()
```

Calls the method to obtain a snapshot list of sub-agent names; safe to iterate over without affecting the orchestrator's internal _sub_agents dict.

### Complexity

Time: O(n) to construct the list from the keys view where n is the number of keys in self._sub_agents. Space: O(n) additional space to hold the returned list.

### Notes

- This method returns a new list as a snapshot; subsequent mutations to self._sub_agents will not change the returned list.
- If self._sub_agents is not present or does not implement .keys(), an attribute or type-related exception (e.g., AttributeError) may occur implicitly.

---



#### async 

![Type: Async](https://img.shields.io/badge/Type-Async-blue)

### Signature

```python
async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]
```

### Description

Implementation not visible

This coroutine is a thin asynchronous wrapper that delegates work to another coroutine on the same object: it awaits and returns the result of self.execute_swarm called with the same task and context arguments. There is no additional processing, validation, or error handling in this function body.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `self` | `implicit instance` | ✅ | Reference to the instance on which the method is invoked.
 |
| `task` | `str` | ✅ | Task argument forwarded to self.execute_swarm.
 |
| `context` | `AgentContext` | ✅ | Context argument forwarded to self.execute_swarm.
 |

### Returns

**Type:** `Dict[str, Any]`

The awaited result returned by self.execute_swarm(task=task, context=context). According to the annotation, this should be a dictionary with string keys and values of any type.


**Possible Values:**

- Any dictionary returned by self.execute_swarm
- Any exception propagated from self.execute_swarm (not handled here)

### Usage Examples

#### Forward a task and context to the swarm executor from an async context

```python
result = await orchestrator.execute(task, context)
```

Demonstrates calling the async wrapper which simply awaits and returns the result of execute_swarm.

### Complexity

O(1) time and O(1) additional space in this wrapper; overall complexity depends on the implementation of self.execute_swarm.

### Related Functions

- `execute_swarm` - Called by this method; this method delegates its work to execute_swarm(task=task, context=context) and returns its awaited result.

### Notes

- The function body contains only a single await of self.execute_swarm and does not perform validation, error handling, or side-effecting operations itself.
- Any side effects, exceptions, or I/O are entirely determined by the implementation of self.execute_swarm, which is not shown here.

---



#### async 

![Type: Async](https://img.shields.io/badge/Type-Async-blue)

### Signature

```python
async def run_single(single_task: str) -> Dict[str, Any]
```

### Description

This asynchronous nested function awaits and returns the result of self.execute_swarm called with the provided single_task and several outer-scope parameters.


run_single is an async wrapper that accepts a single task string and immediately delegates execution to self.execute_swarm using the captured outer-scope variables: context, target_agents, strategy, max_concurrency, timeout, retries, and fail_fast. It does no additional processing of inputs or outputs; it simply awaits and returns whatever execute_swarm returns.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `single_task` | `str` | ✅ | The task identifier or payload to pass through to self.execute_swarm.
<br>**Constraints:** Must be a str (per type annotation) |

### Returns

**Type:** `Dict[str, Any]`

The awaited result returned by self.execute_swarm called with the provided single_task and the captured outer-scope parameters.


**Possible Values:**

- Any dictionary structure that self.execute_swarm returns

### Usage Examples

#### Use within the same scope where run_single is defined to run one task via the swarm executor

```python
result = await run_single("example_task")
```

Awaits execution of 'example_task' by delegating to self.execute_swarm and stores the returned dictionary in result.

### Complexity

O(1) time and O(1) additional space for this wrapper; overall cost depends on the complexity of self.execute_swarm which is invoked and awaited.

### Related Functions

- `self.execute_swarm` - Called by run_single; run_single simply awaits and returns its result.

### Notes

- This function is a thin async passthrough and relies entirely on the behavior of self.execute_swarm.
- The function captures several variables from outer scope (context, target_agents, strategy, max_concurrency, timeout, retries, fail_fast) but does not declare them; they must exist in the enclosing scope.

---



#### async 

![Type: Async](https://img.shields.io/badge/Type-Async-blue)

### Signature

```python
async def run_with_limit(single_task: str) -> Dict[str, Any]
```

### Description

Acquire an existing asynchronous semaphore, await run_single(single_task), and return its result.


This is an asynchronous nested function that uses an outer-scope asynchronous semaphore (accessed via 'async with semaphore') to limit concurrent execution. Inside the semaphore context it awaits the coroutine run_single(single_task) and returns whatever that coroutine returns. The function itself performs no data processing beyond awaiting run_single and does not handle exceptions; any exception raised while acquiring the semaphore or by run_single will propagate to the caller.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `single_task` | `str` | ✅ | A single task identifier or payload string passed through to run_single.
<br>**Constraints:** Must be a str as annotated, No validation performed in this function |

### Returns

**Type:** `Dict[str, Any]`

The dictionary result returned by awaiting run_single(single_task). This function returns that dict unchanged.


**Possible Values:**

- Any dictionary value that run_single(single_task) may return
- If run_single raises, this function will not return and the exception will propagate

### Raises

| Exception | Condition |
| --- | --- |
| `Any exception raised by semaphore acquisition or run_single` | If acquiring the semaphore fails or if run_single(single_task) raises an exception, it propagates out of this function |

### Side Effects

> ❗ **IMPORTANT**
> This function has side effects that modify state or perform I/O operations.

- Acquires and releases the asynchronous semaphore (mutates semaphore internal state)
- Invokes (awaits) run_single(single_task), which may have its own side effects not shown here

### Usage Examples

#### Run a task while ensuring concurrency is limited by an outer semaphore

```python
result = await run_with_limit('task-id-123')
```

Demonstrates awaiting the nested function to get the dictionary result from run_single while respecting the semaphore limit.

### Complexity

O(1) additional time/space complexity for this wrapper; overall cost dominated by run_single(single_task). Semaphore acquire/release is O(1).

### Related Functions

- `run_single` - Called by this function; run_single performs the actual task work and produces the returned Dict[str, Any].

### Notes

- This is a thin wrapper solely to scope semaphore-controlled execution of run_single(single_task).
- The semaphore variable must exist in an enclosing scope and be an asynchronous semaphore supporting 'async with'.
- No exception handling is performed here; callers should handle exceptions from run_single if needed.
- Because the implementation is visible and minimal, no other behaviors are present beyond awaiting run_single inside the semaphore context.

---



#### async 

![Type: Async](https://img.shields.io/badge/Type-Async-blue)

### Signature

```python
async def run_agent(agent_name: str) -> SubAgentResult
```

### Description

Acquires a semaphore and forwards the call to self._execute_single_agent for the given agent_name, returning that awaited result.


This asynchronous inner function accepts a single parameter agent_name (typed as str). It enters an async context manager using the semaphore (captured from the enclosing scope), ensuring the semaphore is acquired for the duration of the call. While holding the semaphore it awaits and returns the result of calling self._execute_single_agent with agent_name and other parameters taken from the enclosing scope (task_map[agent_name], context, timeout, retries). The function itself performs no additional logic beyond semaphore acquisition and forwarding the call and result.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `agent_name` | `str` | ✅ | Name/key of the agent to run; used to index task_map in the call to self._execute_single_agent.
<br>**Constraints:** Must be a valid key for task_map in the enclosing scope (accesses task_map[agent_name]) |

### Returns

**Type:** `SubAgentResult`

The awaited result returned by self._execute_single_agent invoked with the given agent_name and the surrounding context (task, context, timeout, retries).


**Possible Values:**

- Any SubAgentResult instance or value produced by self._execute_single_agent

### Side Effects

> ❗ **IMPORTANT**
> This function has side effects that modify state or perform I/O operations.

- Acquires and releases the async semaphore object from the enclosing scope (async with semaphore)
- Calls (awaits) self._execute_single_agent(...), which may have its own side effects (not visible here)

### Usage Examples

#### Run an agent using the orchestrator's semaphore-controlled worker

```python
await run_agent('agent_1')
```

Shows invoking the async function to execute the agent named 'agent_1'. The call will acquire the shared semaphore, call self._execute_single_agent with parameters from the outer scope, and return its SubAgentResult.

### Complexity

O(1) overhead (constant time and space) for this wrapper function; overall time and space complexity are dominated by self._execute_single_agent and the awaited call.

### Related Functions

- `self._execute_single_agent` - Called by; this function simply awaits and returns its result

### Notes

- This function is an inner async function that relies on several variables from the enclosing scope: semaphore, self, task_map, context, timeout, and retries.
- The implementation here does not validate agent_name beyond indexing task_map; an invalid agent_name will raise a KeyError when task_map[agent_name] is evaluated (propagated from this function).
- Any exceptions raised by self._execute_single_agent propagate through this function unchanged.

---



#### _create_sub_context

![Type: Sync](https://img.shields.io/badge/Type-Sync-green)

### Signature

```python
def _create_sub_context(self, *, parent: AgentContext, sub_agent_name: str) -> AgentContext
```

### Description

Create and return a child AgentContext for a sub-agent when context isolation is enabled; otherwise return the original parent context.


This method checks the instance flag _isolate_context. If _isolate_context is falsy, it returns the provided parent AgentContext unchanged. If _isolate_context is truthy, it constructs a shallow copy of parent.metadata, injects two keys ('swarm_parent' set to the current object's name, and 'sub_agent' set to the provided sub_agent_name), and returns a new AgentContext using the parent's session_id and user_id, the new metadata dict, and a deep copy of the parent's state (using copy.deepcopy) so the returned context's state is isolated from mutations to the parent's state.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `self` | `inferred class instance` | ✅ | The instance of the class containing this method; used to read _isolate_context and name attributes.
<br>**Constraints:** Must have attributes _isolate_context (truthy/falsy) and name (used for metadata) |
| `parent` | `AgentContext` | ✅ | The existing parent AgentContext from which session_id, user_id, metadata, and state are taken.
<br>**Constraints:** Must provide attributes: session_id, user_id, metadata (mapping), and state (picklable for deepcopy) |
| `sub_agent_name` | `str` | ✅ | Name/identifier of the sub-agent to record in the child context metadata under the 'sub_agent' key.
<br>**Constraints:** Should be a string suitable for metadata storage |

### Returns

**Type:** `AgentContext`

Either the original parent AgentContext (if _isolate_context is falsy) or a newly constructed AgentContext with copied session_id and user_id, augmented metadata, and a deep-copied state (if _isolate_context is truthy).


**Possible Values:**

- parent (the same AgentContext instance passed in) if self._isolate_context is falsy
- new AgentContext(session_id=parent.session_id, user_id=parent.user_id, metadata=child_metadata, state=deepcopy(parent.state)) if self._isolate_context is truthy

### Usage Examples

#### When isolation is disabled and you want the sub-agent to share the same context

```python
child = orchestrator._create_sub_context(parent=parent_ctx, sub_agent_name='worker-1')
```

If orchestrator._isolate_context is False, this returns parent_ctx unchanged so the sub-agent will operate on the same context object.

#### When isolation is enabled and you need an isolated context for a sub-agent

```python
child = orchestrator._create_sub_context(parent=parent_ctx, sub_agent_name='worker-1')
```

If orchestrator._isolate_context is True, this returns a new AgentContext with metadata containing 'swarm_parent' and 'sub_agent' and a deep-copied state to avoid shared-state mutations.

### Complexity

Time complexity: O(m + s) where m is the cost to copy parent.metadata (shallow dict copy) and s is the cost of copy.deepcopy on parent.state (depends on size/complexity of state). Space complexity: O(size of new metadata + size of deep-copied state) when isolation is enabled; O(1) additional space when returning parent.

### Related Functions

- `AgentContext` - Constructor called to create the returned context when isolation is enabled
- `copy.deepcopy` - Utility used to deep-copy the parent's state to isolate the child context

### Notes

- The implementation does a shallow copy of parent.metadata via dict(parent.metadata) to avoid mutating the parent's metadata object, then injects 'swarm_parent' and 'sub_agent' keys.
- parent.state must be deepcopy-able (picklable or otherwise supported by copy.deepcopy), otherwise deepcopy may raise an exception at runtime.
- No explicit error handling is present; runtime exceptions from copy.deepcopy or AgentContext construction will propagate to the caller.
- The method relies on the instance attributes _isolate_context and name; their presence and types are assumed by the code.

---



#### _resolve_strategy

![Type: Sync](https://img.shields.io/badge/Type-Sync-green)

### Signature

```python
def _resolve_strategy(strategy: Any) -> SwarmStrategy
```

### Description

Resolve input into a SwarmStrategy: map known string to SEQUENTIAL, return input if already SwarmStrategy, else PARALLEL.


The function accepts any value and resolves it to a SwarmStrategy enum value. If the provided argument is already an instance of SwarmStrategy it is returned unchanged. If the argument is a string, the function strips surrounding whitespace, lowercases it, and compares it to SwarmStrategy.SEQUENTIAL.value; if it matches, SwarmStrategy.SEQUENTIAL is returned. In all other cases (unrecognized strings or other types) the function returns SwarmStrategy.PARALLEL.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `strategy` | `Any` | ✅ | Input to resolve into a SwarmStrategy. Can be an existing SwarmStrategy instance, a string naming a strategy, or any other type.
<br>**Constraints:** If a string, comparison is performed after strip() and lower(), Only the exact value of SwarmStrategy.SEQUENTIAL.value (after strip/lower) maps to SEQUENTIAL, Any other input (including unrecognized strings) resolves to SwarmStrategy.PARALLEL |

### Returns

**Type:** `SwarmStrategy`

A resolved SwarmStrategy value determined from the input.


**Possible Values:**

- The same SwarmStrategy instance passed in (if strategy is already a SwarmStrategy)
- SwarmStrategy.SEQUENTIAL (if strategy is a string equal to SwarmStrategy.SEQUENTIAL.value when stripped and lowercased)
- SwarmStrategy.PARALLEL (default for all other inputs)

### Usage Examples

#### Pass an existing SwarmStrategy instance

```python
_resolve_strategy(SwarmStrategy.SEQUENTIAL)
```

Returns the same SwarmStrategy.SEQUENTIAL instance.

#### Pass a string that names the sequential strategy (possibly with extra whitespace or case differences)

```python
_resolve_strategy('  Sequential  ')
```

After strip() and lower(), matches SwarmStrategy.SEQUENTIAL.value and returns SwarmStrategy.SEQUENTIAL.

#### Pass an unrecognized string or other type

```python
_resolve_strategy('random')
```

Returns SwarmStrategy.PARALLEL as the default fallback.

### Complexity

O(1) time complexity and O(1) space complexity; operations are constant-time type checks and simple string operations.

### Related Functions

- `SwarmStrategy` - Enum referenced by this resolver; function returns values from this enum.

### Notes

- Comparison for string inputs is case-insensitive and ignores leading/trailing whitespace.
- Only the specific value SwarmStrategy.SEQUENTIAL.value (after normalizing) maps to SEQUENTIAL; everything else maps to PARALLEL.
- Function does not perform validation beyond the explicit checks shown; unexpected types are quietly mapped to PARALLEL.

---



#### _coerce_bool

![Type: Sync](https://img.shields.io/badge/Type-Sync-green)

### Signature

```python
def _coerce_bool(value: Any) -> bool
```

### Description

Convert an input value to a boolean according to simple heuristics implemented in the function body.


The function inspects the provided value and returns a boolean. If the value is already a bool it is returned unchanged. If the value is a str, the string is trimmed and lower-cased and then considered True if it matches one of the literal tokens "1", "true", "yes", or "on"; otherwise it is False. For any other type, the built-in bool() conversion is applied and its result returned.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `value` | `Any` | ✅ | The input to convert to a boolean. Can be a bool, str, or any other type.
<br>**Constraints:** If value is a str, whitespace is stripped and comparison is case-insensitive, No other validation is performed |

### Returns

**Type:** `bool`

A boolean representing the coerced truthiness of the input following the function's rules.


**Possible Values:**

- True
- False

### Usage Examples

#### Convert common string representations of truthy values to True

```python
_coerce_bool(' yes ')
```

Whitespace is stripped and comparison is case-insensitive, so this returns True.

#### Return a bool unchanged

```python
_coerce_bool(False)
```

A boolean input is returned as-is (False).

#### Fallback to Python truthiness for non-string, non-bool inputs

```python
_coerce_bool(0)
```

For numeric types the builtin bool() is used; 0 becomes False, nonzero becomes True.

### Complexity

Time: O(m) where m is the length of the string when input is a str (strip() and lower() operate over the string); otherwise O(1). Space: O(1) additional space (aside from temporary string operations).

### Notes

- Recognized truthy string tokens are exactly: "1", "true", "yes", "on" (case-insensitive after stripping).
- Any other string, including "0", "false", "no", or arbitrary text, will be treated as False by this function.
- This function does not raise exceptions explicitly; however, non-str types that implement __bool__/__len__ determine bool(value).

---



#### _coerce_int

![Type: Sync](https://img.shields.io/badge/Type-Sync-green)

### Signature

```python
def _coerce_int(value: Any, *, default: int) -> int
```

### Description

Attempt to convert the given value to an int and return it; if conversion fails with TypeError or ValueError, return the provided default.


The function calls the built-in int() on the provided value and returns the resulting integer. It wraps the conversion in a try/except block that catches TypeError and ValueError raised by int(value). If either of those exceptions occurs, the function returns the caller-supplied default integer. No other exceptions are caught, so any other exception raised by int(value) will propagate out of this function.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `value` | `Any` | ✅ | The value to be converted to int using the built-in int().
<br>**Constraints:** May be any object accepted by int(); if int(value) raises TypeError or ValueError, the function returns default. |
| `default` | `int` | ✅ | Keyword-only integer to return if conversion fails with TypeError or ValueError.
<br>**Constraints:** Should be an int (the function will return it unchanged when conversion fails)., Mandatory as a keyword-only argument due to the '*' in the signature. |

### Returns

**Type:** `int`

An integer result: either int(value) if conversion succeeded, or the provided default if conversion raised TypeError or ValueError.


**Possible Values:**

- int(value) when conversion succeeds
- default when int(value) raises TypeError or ValueError

### Raises

| Exception | Condition |
| --- | --- |
| `Any exception other than TypeError or ValueError raised by int(value)` | If int(value) raises an exception not caught by the function (i.e., not TypeError or ValueError), that exception will propagate out of _coerce_int. |

### Usage Examples

#### When you have a value that might not be convertible to int and you want a fallback

```python
_coerce_int('42', default=0)
```

Returns 42 because the string '42' converts successfully to int.

#### When conversion fails and you want a default

```python
_coerce_int('not-an-int', default=10)
```

int('not-an-int') raises ValueError, so the function returns the provided default 10.

#### When value is None

```python
_coerce_int(None, default=5)
```

int(None) raises TypeError, so the function returns the default 5.

### Complexity

O(1) time complexity and O(1) space complexity (single call to int() and constant-time control flow).

### Related Functions

- `int` - Calls the built-in int() function to perform the conversion.

### Notes

- The default parameter is keyword-only due to the '*' in the signature.
- TypeError and ValueError from int(value) are suppressed and cause the default to be returned.
- Other exceptions raised by int(value) (if any) are not caught and will propagate to the caller.

---



#### _coerce_timeout

![Type: Sync](https://img.shields.io/badge/Type-Sync-green)

### Signature

```python
def _coerce_timeout(value: Any) -> Optional[float]
```

### Description

Attempt to convert the provided value to a positive float; return that float if > 0, otherwise return None.


The function accepts any input and tries to coerce it into a floating-point timeout value. If the input is None, it immediately returns None. It then attempts to cast the input to float; if casting raises TypeError or ValueError the function returns None. If casting succeeds, the function returns the resulting float only when it is strictly greater than 0; non-positive values (zero or negative) result in None.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `value` | `Any` | ✅ | An input that should represent a timeout value; may be None, a number, or a string convertible to float.
<br>**Constraints:** If None => function returns None, If not convertible to float => function returns None, If float(value) <= 0 => function returns None, Only positive floats (> 0) are returned |

### Returns

**Type:** `Optional[float]`

A positive float representation of the input timeout, or None if input is None, not convertible to float, or not strictly positive.


**Possible Values:**

- None (when input is None, not convertible to float, or float(value) <= 0)
- float > 0 (when input is convertible to float and the numeric value is strictly greater than 0)

### Usage Examples

#### Convert a numeric string to a positive timeout

```python
_coerce_timeout('2.5')
```

Returns 2.5 as a float because the string is convertible and greater than 0.

#### Handle None input

```python
_coerce_timeout(None)
```

Returns None immediately because the input is None.

#### Reject non-convertible or non-positive values

```python
_coerce_timeout('abc')  # or _coerce_timeout(0) or _coerce_timeout(-1)
```

Returns None because 'abc' cannot be converted to float, and 0 or -1 are not strictly positive.

### Complexity

O(1) time and O(1) space: operations consist of a constant number of checks and a single float conversion.

### Notes

- The function treats zero and negative numbers as invalid and returns None for them.
- TypeError and ValueError from float() are caught and handled by returning None.
- The function does not log, raise, or modify any external state.

---


