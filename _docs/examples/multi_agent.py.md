<details>
<summary>Documentation Metadata (click to expand)</summary>

```json
{
  "doc_type": "file_overview",
  "file_path": "examples/multi_agent.py",
  "source_hash": "9465ebb4c5b4ac4e1b5ce62eb1d1311596f73d68380acf69f00d7f88e93b6623",
  "last_updated": "2026-02-19T18:53:44.063306+00:00",
  "tokens_used": 24660,
  "complexity_score": 3,
  "estimated_review_time_minutes": 10,
  "external_dependencies": []
}
```

</details>

[Documentation Home](../README.md) > [examples](./README.md) > **multi_agent**

---

# multi_agent.py

> **File:** `examples/multi_agent.py`

![Complexity: Low](https://img.shields.io/badge/Complexity-Low-green) ![Review Time: 10min](https://img.shields.io/badge/Review_Time-10min-blue)

## 📑 Table of Contents


- [Overview](#overview)
- [Dependencies](#dependencies)
- [Architecture Notes](#architecture-notes)
- [Usage Examples](#usage-examples)
- [Maintenance Notes](#maintenance-notes)
- [Functions and Classes](#functions-and-classes)

---

## Overview

This file provides a runnable example that constructs a SwarmOrchestrator, registers multiple sub-agents, and demonstrates two workflows: a single swarm operation and a mass swarm operation (multiple tasks). It defines two simple agent classes (WorkerAgent and FlakyWorkerAgent) that inherit from BaseAgent and implement async execute(...) methods. The script configures the orchestrator using SwarmStrategy.PARALLEL, max_concurrency, sub_agent_timeout, and sub_agent_retries, and then invokes execute_swarm and execute_mass_swarm while passing an AgentContext containing session_id and user_id.

Implementation details include asynchronous operations (async/await) with small asyncio.sleep calls to simulate work or delays. FlakyWorkerAgent deliberately fails on its first call (raises RuntimeError) and succeeds on subsequent calls by tracking an instance attribute _calls. The example also mutates sys.path at runtime (sys.path.insert) to allow a top-level import from src.agents when run as a standalone script. The script is intended as documentation and quick verification of the swarm orchestration API: it shows how to register sub-agents via orchestrator.add_sub_agents, list registered agents via orchestrator.list_sub_agents(), and call orchestrator.execute_swarm / orchestrator.execute_mass_swarm with an AgentContext.

## Dependencies

### Internal Dependencies

| Module | Usage |
| --- | --- |
| `asyncio` | Used for async support: asyncio.sleep(...) is called inside agent execute methods to simulate work; asyncio.run(main()) is used in the module entrypoint to run the top-level async main function. |
| `logging` | Configures basic logging via logging.basicConfig(level=logging.INFO) and obtains a logger via logging.getLogger(__name__) for potential informational logging; present in the example but not used heavily beyond setup. |
| `sys` | sys.path.insert(0, str(Path(__file__).parent.parent)) is used to prepend the repository root to Python path so the local package import from src.agents works when running the example as a script. |
| [pathlib.Path](../pathlib/Path.md) | The Path class is imported (from pathlib import Path) and used to compute the parent directory of the file (__file__).parent.parent to build a path inserted into sys.path for local module resolution. |
| `typing` | Provides typing hints used in signatures: Any and Dict are imported and used in method signatures and return type annotations (e.g., async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]). |
| [src.agents](../src/agents.md) | An internal project module: from src.agents import AgentContext, BaseAgent, SwarmOrchestrator, SwarmStrategy. The example creates AgentContext(session_id=..., user_id=...), subclasses BaseAgent to implement WorkerAgent and FlakyWorkerAgent execute methods, constructs a SwarmOrchestrator instance and calls its methods add_sub_agents, list_sub_agents, execute_swarm, and execute_mass_swarm. SwarmStrategy.PARALLEL is used to configure orchestrator strategy. |

## 📁 Directory

This file is part of the **examples** directory. View the [directory index](_docs/examples/README.md) to see all files in this module.

## Architecture Notes

- Async/Await pattern: The example uses async def for agent execution methods and the main routine, and uses asyncio.run(main()) at the script entrypoint. Agent execute methods call asyncio.sleep to simulate asynchronous work.
- Swarm orchestration: A SwarmOrchestrator (from src.agents) is configured with a strategy (SwarmStrategy.PARALLEL), max_concurrency, sub_agent_timeout, and sub_agent_retries. The orchestrator is responsible for dispatching tasks to registered sub-agents and collecting reports (execute_swarm and execute_mass_swarm).
- Transient failure simulation: FlakyWorkerAgent maintains an instance attribute _calls to fail on the first invocation (raises RuntimeError) and succeed thereafter. This demonstrates how orchestrator retry behavior (sub_agent_retries) interacts with transient errors.
- Local import resolution: The script mutates sys.path to allow importing the local src.agents package when executed from examples/; this is a pragmatic decision for example scripts but can be brittle in other environments.

## Usage Examples

### Single swarm operation

main() constructs SwarmOrchestrator("swarm_controller", config) where config includes strategy=SwarmStrategy.PARALLEL.value, max_concurrency=4, sub_agent_timeout=5, sub_agent_retries=1. It registers WorkerAgent('worker_1'), WorkerAgent('worker_2'), WorkerAgent('worker_3'), and FlakyWorkerAgent('flaky_worker') via orchestrator.add_sub_agents(...). It creates AgentContext(session_id='swarm_demo_session', user_id='demo_user') and calls await orchestrator.execute_swarm('Analyze quarterly metrics', context). The orchestrator dispatches the single task to each registered sub-agent concurrently (per PARALLEL strategy), each agent's execute receives the task string and context and returns a Dict with keys like 'success', 'agent', 'task', and optionally 'session' or 'attempt'. FlakyWorkerAgent fails on its first attempt but can succeed on retry when orchestrator honors sub_agent_retries=1.

### Mass swarm operation (multiple tasks)

main() calls await orchestrator.execute_mass_swarm(tasks=[...], context=context, parallel_tasks=True) to run multiple different task strings across the registered sub-agents. With parallel_tasks=True, the orchestrator processes tasks concurrently subject to max_concurrency. The mass swarm returns an aggregate report with keys printed by the example: 'success', 'successful_tasks', and 'failed_tasks'. This demonstrates batching/mass-orchestration behavior and how per-sub-agent retries and timeouts can affect mass run success.

## Maintenance Notes

- Performance: The example uses fixed asyncio.sleep delays inside agents to simulate work; real agent implementations will replace sleeps with actual I/O/compute. Adjust max_concurrency and sub_agent_timeout in orchestrator config for production workloads to avoid resource exhaustion or premature timeouts.
- Testing and reliability: FlakyWorkerAgent stores state in an instance attribute (_calls). When testing multi-run scenarios, be aware that the agent instance retains call count across tasks; create fresh agent instances per test if isolation is required. The example intentionally demonstrates transient failure handling — ensure orchestrator's retry behavior aligns with real failure semantics.
- Portability: The script mutates sys.path to import src.agents. For CI or packaged deployment, prefer installing the package or running from repository root rather than relying on sys.path modification.
- Error handling: The example relies on SwarmOrchestrator to handle sub-agent exceptions and aggregate success/failure reports. When extending agents, raise clear exception types for transient vs permanent failures to allow orchestrator retry logic to make informed decisions.
- Extensions: Consider adding CLI arguments or environment-driven configuration to parameterize orchestrator settings (strategy, concurrency, timeouts, retries) rather than hard-coding them in the example.

---

## Navigation

**↑ Parent Directory:** [Go up](_docs/examples/README.md)

---

*This documentation was automatically generated by AI ([Woden DocBot](https://github.com/marketplace/ai-document-creator)) and may contain errors. It is the responsibility of the user to validate the accuracy and completeness of this documentation.*


---

## Functions and Classes


#### async 

![Type: Async](https://img.shields.io/badge/Type-Async-blue)

### Signature

```python
async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]
```

### Description

Pause briefly (0.05s) and return a dictionary summarizing a successful execution including the agent name, the provided task, and the session id from the context.


This asynchronous method awaits asyncio.sleep for 0.05 seconds and then constructs and returns a dictionary with four keys: 'success' (always True), 'agent' (taken from self.name), 'task' (the task argument passed in), and 'session' (taken from context.session_id). There is no additional logic, validation, or mutation of inputs beyond reading self.name and context.session_id.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `task` | `str` | ✅ | A string describing the task to be included in the returned summary.
 |
| `context` | `AgentContext` | ✅ | An AgentContext object whose session_id attribute is read and included in the returned dictionary.
 |

### Returns

**Type:** `Dict[str, Any]`

A dictionary containing execution metadata: 'success' (bool), 'agent' (value of self.name), 'task' (echo of the task parameter), and 'session' (value of context.session_id).


**Possible Values:**

- {"success": True, "agent": <self.name>, "task": <task>, "session": <context.session_id>}

### Usage Examples

#### Call from asynchronous code to get a quick success summary for a task

```python
result = await agent.execute("process_item", context)
```

Demonstrates awaiting the async method and receiving a dictionary with success, agent name, task string, and session id.

### Complexity

Time complexity: O(1) (constant work plus a fixed sleep). Space complexity: O(1) (returns a small fixed-size dictionary).

### Related Functions

- `asyncio.sleep` - calls

### Notes

- The method always returns 'success': True as per the implementation.
- The method reads self.name and context.session_id; ensure those attributes exist on the instance and context respectively.
- The function contains a fixed await asyncio.sleep(0.05) which introduces a small delay before the return.

---



#### __init__

![Type: Sync](https://img.shields.io/badge/Type-Sync-green)

### Signature

```python
def __init__(self, name: str, config: Dict[str, Any] = None) -> None
```

### Description

Call the superclass constructor with the provided name and config, then initialize this instance's _calls attribute to 0.


This initializer invokes the parent class's __init__ method with the exact name and config arguments passed in, ensuring any initialization performed by the superclass is executed. After the superclass initialization returns, it sets an instance attribute _calls to the integer 0. There is no other logic, validation, or returned value.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | `str` | ✅ | A name value that is forwarded unchanged to the superclass __init__.
 |
| `config` = `None` | `Dict[str, Any]` | ❌ | An optional configuration mapping that is forwarded unchanged to the superclass __init__.
 |

### Returns

**Type:** `None`

Constructors in Python do not return a value; this method returns None implicitly.


**Possible Values:**

- None

### Side Effects

> ❗ **IMPORTANT**
> This function has side effects that modify state or perform I/O operations.

- Calls the superclass __init__ method (super().__init__(name, config)) which may perform additional initialization
- Sets the instance attribute self._calls to 0 (mutates object state)

### Usage Examples

#### Create an instance of the class (constructor is invoked automatically)

```python
obj = ClassName('agent_name')
```

Demonstrates calling the constructor with only the required name parameter; config defaults to None. The superclass __init__ is invoked and obj._calls is initialized to 0.

#### Create an instance with a configuration mapping

```python
obj = ClassName('agent_name', {'key': 'value'})
```

Shows passing a config dict to be forwarded to the superclass __init__, and _calls will be set to 0 afterwards.

### Complexity

O(1) time and O(1) space — performs a constant number of operations regardless of input sizes.

### Related Functions

- `__init__ (superclass)` - Called by this method to perform parent-class initialization

### Notes

- No validation is performed on name or config in this implementation; values are forwarded directly to the superclass.
- Behavior of overall initialization may depend on the superclass implementation invoked via super().__init__.

---



#### async 

![Type: Async](https://img.shields.io/badge/Type-Async-blue)

### Signature

```python
async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]
```

### Description

Increment an instance call counter, simulate a short asynchronous delay, and return a result dictionary; on the first invocation it raises a RuntimeError to simulate a transient failure.


This async method increments the instance attribute self._calls each time it is invoked. If the incremented counter equals 1 (i.e., the first call), it raises a RuntimeError with message "Transient worker failure". Otherwise it awaits asyncio.sleep(0.02) to introduce a short asynchronous delay and then returns a dictionary containing keys: "success" (True), "agent" (the instance's self.name), "task" (the provided task argument), and "attempt" (the current value of self._calls).

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `self` | `implicit instance` | ✅ | The instance on which the method is called; used to access and modify instance attributes (notably self._calls and self.name).
<br>**Constraints:** Must have attributes _calls (numeric) and name (string or convertible to expected representation) |
| `task` | `str` | ✅ | A task identifier or description that is returned in the result dictionary under the "task" key.
<br>**Constraints:** Should be a string (annotation indicates str) |
| `context` | `AgentContext` | ✅ | Context object passed to the method but not inspected or used by this implementation; included for API compatibility.
<br>**Constraints:** No constraints enforced by this implementation (not accessed) |

### Returns

**Type:** `Dict[str, Any]`

A dictionary with execution metadata when the method completes normally.


**Possible Values:**

- {"success": True, "agent": self.name, "task": task, "attempt": self._calls}
- Raises RuntimeError instead of returning when self._calls == 1

### Raises

| Exception | Condition |
| --- | --- |
| `RuntimeError` | Raised when the instance attribute self._calls equals 1 immediately after incrementing (i.e., on the first invocation) with message "Transient worker failure". |

### Side Effects

> ❗ **IMPORTANT**
> This function has side effects that modify state or perform I/O operations.

- Increments/modifies the instance attribute self._calls
- Awaits asyncio.sleep(0.02) which suspends the coroutine for ~0.02 seconds (asynchronous delay)

### Usage Examples

#### Retrying an operation where the first call simulates a transient failure

```python
result = await agent.execute("do_work", context)
```

On the first call this will raise RuntimeError. Subsequent calls will await for ~0.02s and return a dict with success True and attempt count.

#### Checking returned metadata after a successful invocation

```python
await agent.execute("taskA", context)  # may raise on first call
# after a successful call
res = await agent.execute("taskA", context)
# res == {"success": True, "agent": agent.name, "task": "taskA", "attempt": <int>}
```

Demonstrates that the method returns a dict containing the task, agent name, and the number of attempts (self._calls).

### Complexity

Time complexity: O(1) — performs a fixed number of operations regardless of input size (increment, conditional, sleep, return). Space complexity: O(1) — returns a small fixed-size dict.

### Related Functions

- `__init__` - Constructor likely initializes self._calls and self.name which this method reads and updates

### Notes

- The context parameter is accepted but not used in this implementation; it exists for API compatibility.
- The method intentionally raises a RuntimeError on the first call to simulate a transient worker failure; callers should handle or retry accordingly.
- asyncio.sleep is awaited to simulate asynchronous work; this does not perform external I/O but does suspend the coroutine.

---



#### main

![Type: Async](https://img.shields.io/badge/Type-Async-blue)

### Signature

```python
async def main() -> None
```

### Description

Demonstration async routine that builds a SwarmOrchestrator, registers worker agents, creates an AgentContext, runs single and mass swarm tasks, and prints progress and summaries.


This asynchronous function is an example/demo routine. It prints an introductory message, constructs a SwarmOrchestrator instance with a specific strategy and options, registers a list of WorkerAgent and FlakyWorkerAgent instances via add_sub_agents (mutating the orchestrator's registered sub-agents), creates an AgentContext, prints the registered sub-agents, then invokes orchestrator.execute_swarm for a single task and awaits the result, printing a summary report. It then invokes orchestrator.execute_mass_swarm with multiple tasks (parallel_tasks=True), awaits the mass report, and prints a summary. Finally it prints a completion message. The function does not return a value (returns None).

### Returns

**Type:** `None`

This function does not explicitly return a value; it returns None after completion.


**Possible Values:**

- None

### Side Effects

> ❗ **IMPORTANT**
> This function has side effects that modify state or perform I/O operations.

- Prints multiple informational lines to standard output using print()
- Instantiates SwarmOrchestrator and AgentContext objects
- Registers sub-agents by calling orchestrator.add_sub_agents(...) which mutates the orchestrator's internal state (registered sub-agents)
- Calls and awaits asynchronous orchestrator methods: execute_swarm(...) and execute_mass_swarm(...), which perform asynchronous operations (their internal side effects are not visible in this function)
- Reads the list of registered sub-agents via orchestrator.list_sub_agents()

### Usage Examples

#### Run the demo main routine in an async-aware entry point

```python
import asyncio

asyncio.run(main())
```

Demonstrates how to execute this async demo function from a synchronous script entry point; will run the sequence of prints, registrations, and awaited orchestrator operations shown in the example.

### Complexity

The function itself performs a fixed number of operations (O(1) time and O(1) additional space) aside from the asynchronous orchestrator calls; the time and space complexity of the awaited operations depend on the implementations of SwarmOrchestrator.execute_swarm and execute_mass_swarm and are not determined from this code.

### Related Functions

- `SwarmOrchestrator.__init__` - Called to construct the orchestrator instance used by this function
- `SwarmOrchestrator.add_sub_agents` - Called to register sub-agents; mutates orchestrator state
- `SwarmOrchestrator.list_sub_agents` - Called to retrieve the registered sub-agents for printing
- `SwarmOrchestrator.execute_swarm` - Awaited to perform a single swarm operation and obtain a report
- `SwarmOrchestrator.execute_mass_swarm` - Awaited to perform multiple swarm tasks and obtain a mass report
- `AgentContext.__init__` - Called to construct the context object passed to orchestrator methods

### Notes

- This function is an example/demo meant to illustrate usage; it relies on types and implementations (SwarmOrchestrator, WorkerAgent, FlakyWorkerAgent, AgentContext, SwarmStrategy) defined elsewhere in the codebase.
- No error handling is present in this function; exceptions raised by the orchestrator methods or agent constructors will propagate to the caller.
- The function prints formatted report dictionaries assuming execute_swarm and execute_mass_swarm return mapping-like objects with keys used in the prints ('success', 'successful_agents', 'failed_agents', 'successful_tasks', 'failed_tasks').

---


