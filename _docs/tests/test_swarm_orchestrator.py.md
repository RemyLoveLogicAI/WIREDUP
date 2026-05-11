<details>
<summary>Documentation Metadata (click to expand)</summary>

```json
{
  "doc_type": "file_overview",
  "file_path": "tests/test_swarm_orchestrator.py",
  "source_hash": "cb9ea96cec0a459f92059f22a7c55d42497fc485f4852565f1138fa4369a3b49",
  "last_updated": "2026-02-19T18:57:29.950248+00:00",
  "tokens_used": 56309,
  "complexity_score": 3,
  "estimated_review_time_minutes": 10,
  "external_dependencies": [
    "pytest"
  ]
}
```

</details>

[Documentation Home](../README.md) > [tests](./README.md) > **test_swarm_orchestrator**

---

# test_swarm_orchestrator.py

> **File:** `tests/test_swarm_orchestrator.py`

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

This file contains unit/integration tests for the SwarmOrchestrator class from src.agents. It defines three lightweight test agent subclasses (EchoWorker, FlakyWorker, AlwaysFailWorker) that inherit from BaseAgent and implement an async execute(task: str, context: AgentContext) -> Dict[str, Any] method. The tests instantiate SwarmOrchestrator with different configuration maps (strategy, max_concurrency, sub_agent_retries, sub_agent_timeout, fail_fast, max_task_concurrency, etc.), add sub-agents via add_sub_agent/add_sub_agents, and then call execute_swarm or execute_mass_swarm while asserting on the returned report structure and on side effects (e.g., agent.calls counters and context.state['swarm_history']). The helper agents are used as deterministic test doubles: EchoWorker sleeps for a configured delay and returns metadata, FlakyWorker raises a RuntimeError on its first call then succeeds, and AlwaysFailWorker always raises a RuntimeError.

The test cases illustrate the expected public behavior and report shape produced by SwarmOrchestrator: parallel vs sequential execution, targeted agent selection and sub-task overrides, retry semantics that should recover a transient failure, sub-agent timeout marking a timed-out result with an error message, fail-fast behavior in sequential mode where subsequent agents are skipped and marked with attempts == 0 and an explanatory error, and the execute_mass_swarm API running multiple task operations with concurrency controls that produce an operations list and update AgentContext.state['swarm_history']. Tests rely on asyncio and use pytest.mark.asyncio to run async test coroutines. This file does not call external APIs or services; it interacts solely with in-repo classes and Python standard-library asyncio for timing/sleep behavior.

## Dependencies

### External Dependencies

| Module | Usage |
| --- | --- |
| `pytest` | Provides the pytest.mark.asyncio decorator to run async test coroutines. Tests are declared as async def and decorated with @pytest.mark.asyncio. pytest is a third-party testing framework (is_external=true). |

### Internal Dependencies

| Module | Usage |
| --- | --- |
| `asyncio` | Used directly in test helper agents: EchoWorker.execute calls await asyncio.sleep(self.delay) to simulate work and controllable delays. Marked as a language standard library; no external installation required. |
| `typing` | Imports type annotations Any and Dict used in helper agent execute signatures and return types (e.g., async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]; used only for static typing and readability). Part of the Python standard library. |
| [src.agents](../src/agents.md) | Internal project module: imports AgentContext, BaseAgent, SwarmOrchestrator, SwarmStrategy which are directly referenced in the tests and in helper agent type annotations. Tests instantiate SwarmOrchestrator, create AgentContext(session_id=...), and subclass BaseAgent for test doubles. Marked as internal to the repository (is_external=false). |

## 📁 Directory

This file is part of the **tests** directory. View the [directory index](_docs/tests/README.md) to see all files in this module.

## Architecture Notes

- Async/await concurrency: Tests and helper agents are implemented with async def and use asyncio.sleep to simulate asynchronous work. Tests use pytest.mark.asyncio to run coroutine-based test functions.
- Test harness pattern: The file defines small in-file test doubles (EchoWorker, FlakyWorker, AlwaysFailWorker) that subclass BaseAgent and provide deterministic behaviors (echo metadata, transient failure, permanent failure) to exercise orchestrator policies (retries, timeouts, fail-fast).
- Configuration-driven orchestrator behavior: Tests instantiate SwarmOrchestrator with configuration dicts (e.g., {'strategy': SwarmStrategy.PARALLEL.value, 'max_concurrency': 6}) to exercise parallel vs sequential strategies, concurrency limits, retry counts, per-sub-agent timeout, and fail_fast behavior. The orchestrator is expected to return structured reports with keys such as 'success', 'total_agents', 'results', 'failed_agents', 'successful_agents', and for mass swarm 'total_tasks', 'operations'.
- State and side-effects: execute_mass_swarm is expected to append entries to AgentContext.state['swarm_history'], and individual helper agents maintain a calls counter to assert how many times execute was invoked.
- Error handling approach under test: The tests assert that timeouts produce a result entry with 'timed_out' == True and an error string containing 'Timed out after', that retries increment attempts and can recover transient failures, and that fail_fast in sequential mode results in subsequent agents being skipped with attempts == 0 and an explanatory error string.

## Usage Examples

### Parallel execution across many sub-agents

Create a SwarmOrchestrator configured for parallel strategy and a max_concurrency (example in test_parallel_swarm_executes_all_sub_agents). Add multiple EchoWorker instances with default small delays via add_sub_agents. Call await orchestrator.execute_swarm('parallel-task', AgentContext(session_id='parallel')). The expected report has 'success': True, total_agents equal to number added (12 in test), successful_agents equal to total_agents, failed_agents == 0, and every entry in report['results'] contains a dict with 'success' True and the echo metadata returned by each EchoWorker.

### Targeted execution and per-agent sub-task override

Create SwarmOrchestrator with default configuration. Add two EchoWorker instances named 'worker_a' and 'worker_b'. Call execute_swarm with target_agents=['worker_a'] and sub_tasks mapping that provides custom task strings per agent. The orchestrator should only run 'worker_a', use the sub_tasks mapping to pass 'custom-task-for-a' to that agent, return total_agents == 1, and other agent's calls counter remains 0.

### Retry policy recovers a flaky worker

Register a FlakyWorker that raises on its first call and succeeds on subsequent calls. Instantiate SwarmOrchestrator with 'sub_agent_retries': 1 and sequential strategy. Calling execute_swarm will attempt the flaky worker up to 2 times; the report should show success True, the first result success True with 'attempts' == 2, and the FlakyWorker.calls == 2 to confirm retries executed.

### Timeout marks a sub-agent as failed

Add an EchoWorker configured with a delay greater than SwarmOrchestrator's 'sub_agent_timeout'. Configure orchestrator with sub_agent_timeout small (0.01) and sub_agent_retries 0. Calling execute_swarm should mark that agent's result with 'success' False, 'timed_out' True, and an error message containing 'Timed out after'; the overall report.success should be False and failed_agents should include that agent.

## Maintenance Notes

- Timing/flakiness: Tests use real asyncio.sleep to simulate work; short timeouts and small delays may lead to nondeterministic behavior on slow CI machines. Consider replacing explicit sleeps with injected clock or mocking asyncio.sleep where determinism is required.
- Test isolation: Helper agents keep a calls attribute mutated across tests. Ensure tests do not share the same agent instances across test functions (current tests instantiate fresh agents per test). If reusing agents, reset counters between tests.
- Assertions tied to report shape: Tests assert on specific report keys and nested result fields (e.g., 'timed_out', 'attempts', 'error' messages). If SwarmOrchestrator's report schema changes, update tests accordingly. Prefer using more focused assertions if the report becomes more complex.
- Timeout and retry interactions: The tests assume orchestrator applies per-sub-agent timeouts independently of retries and that retries increment the per-agent attempt counter. If orchestration semantics change (e.g., global time budget, exponential backoff), adjust tests and helper agents to reflect new expectations.
- Opportunity: Introduce parametrized tests to cover additional combinations of strategy, concurrency and retry settings, and to reduce duplicated test scaffolding. Also consider adding explicit assertions for ordering in sequential strategy tests.

---

## Navigation

**↑ Parent Directory:** [Go up](_docs/tests/README.md)

---

*This documentation was automatically generated by AI ([Woden DocBot](https://github.com/marketplace/ai-document-creator)) and may contain errors. It is the responsibility of the user to validate the accuracy and completeness of this documentation.*


---

## Functions and Classes


#### __init__

![Type: Sync](https://img.shields.io/badge/Type-Sync-green)

### Signature

```python
def __init__(self, name: str, delay: float = 0.01)
```

### Description

Initializes the instance by delegating to the superclass initializer with name, and sets two instance attributes: delay and calls.


This constructor calls the parent class's __init__ method with the provided name parameter, then stores the provided delay value on the instance as self.delay and initializes a counter attribute self.calls to 0. The method contains no return statement and performs only simple attribute assignments and a call to the superclass initializer.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | `str` | ✅ | A name value passed to the superclass initializer; used only by the call to super().__init__(name).
 |
| `delay` = `0.01` | `float` | ❌ | A numeric value stored on the instance as self.delay.
 |

### Returns

**Type:** `None`

Constructors in Python do not return a value; this method returns None implicitly.


**Possible Values:**

- None

### Side Effects

> ❗ **IMPORTANT**
> This function has side effects that modify state or perform I/O operations.

- Calls super().__init__(name)
- Assigns self.delay = delay
- Assigns self.calls = 0

### Usage Examples

#### Instantiate an object of the class to initialize name, delay and reset calls counter

```python
instance = SomeClass('worker-name', 0.05)
```

Creates an instance, invokes the superclass initializer with 'worker-name', sets instance.delay to 0.05 and initializes instance.calls to 0.

### Complexity

O(1) time and O(1) additional space

### Related Functions

- `__init__ (superclass)` - Calls: this initializer invokes the parent class's __init__ method with the name argument

### Notes

- No validation is performed on the parameters in this implementation; values are stored as provided.
- Because the constructor calls super().__init__(name), behavior may depend on the parent class implementation.

---



#### async 

![Type: Async](https://img.shields.io/badge/Type-Async-blue)

### Signature

```python
async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]
```

### Description

Increments an instance call counter, awaits a configured delay, and returns a dictionary containing a success flag, the agent name, the provided task string, and the session_id from the AgentContext.


This asynchronous method performs three observable actions in sequence: it increments self.calls by 1, awaits asyncio.sleep(self.delay) to introduce an asynchronous delay based on the instance's delay attribute, and then constructs and returns a dict with fixed keys 'success', 'agent', 'task', and 'session_id'. The 'agent' value is taken from self.name and 'session_id' is read from context.session_id. No branching or error handling is present in the implementation.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `self` | `no type annotation (instance reference)` | ✅ | Reference to the instance; used to read and modify instance attributes (self.calls, self.delay, self.name).
<br>**Constraints:** Must have attributes: calls (numeric), delay (number), name (string) |
| `task` | `str` | ✅ | A string describing the task; included verbatim in the returned dictionary under the 'task' key.
<br>**Constraints:** Should be a string (no validation is performed in the method) |
| `context` | `AgentContext` | ✅ | An object providing at least a session_id attribute; its session_id is included in the returned dictionary.
<br>**Constraints:** Must have attribute 'session_id' (accessed as context.session_id). |

### Returns

**Type:** `Dict[str, Any]`

A dictionary with four keys: 'success' (bool True), 'agent' (value of self.name), 'task' (the provided task string), and 'session_id' (value of context.session_id).


**Possible Values:**

- {'success': True, 'agent': <self.name>, 'task': <task>, 'session_id': <context.session_id>}

### Side Effects

> ❗ **IMPORTANT**
> This function has side effects that modify state or perform I/O operations.

- Increments instance attribute self.calls by 1 (mutates instance state)
- Performs an asynchronous sleep via asyncio.sleep(self.delay) (schedules a non-blocking delay)

### Usage Examples

#### Call from async context to execute a task with a given AgentContext

```python
result = await instance.execute('do-work', context)
```

Demonstrates awaiting the asynchronous execute method; result will be a dict containing success, agent, task, and session_id after the configured delay and after self.calls has been incremented.

### Complexity

Time complexity: O(1) aside from the awaited delay (constant-time operations). Space complexity: O(1) additional memory for the returned dictionary.

### Related Functions

- `None visible in snippet` - No other related functions are called by or shown in this implementation; it directly calls asyncio.sleep.

### Notes

- The method directly accesses and mutates instance attributes: self.calls, self.delay, and self.name must exist on the instance.
- No input validation or error handling is present; if context lacks session_id or self attributes are missing, an AttributeError will be raised by Python at runtime.
- The function calls asyncio.sleep which yields control; callers must run this inside an async event loop.

---



#### __init__

![Type: Sync](https://img.shields.io/badge/Type-Sync-green)

### Signature

```python
def __init__(self, name: str)
```

### Description

Initializes the instance by delegating initialization to the superclass with the provided name and setting an instance counter attribute calls to 0.


This constructor calls the superclass __init__ method with the given name argument, ensuring any parent initialization logic runs. After that, it creates or resets an instance attribute named calls and sets it to 0. There are no return statements; initialization is performed via side effects on the instance.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | `str` | ✅ | A name value passed through to the superclass constructor.
<br>**Constraints:** No validation performed in this method; any constraints are those imposed by the superclass __init__ (if any). |

### Returns

**Type:** `None`

Constructors in Python do not return a value; the method returns None implicitly after initializing the instance.


**Possible Values:**

- None

### Side Effects

> ❗ **IMPORTANT**
> This function has side effects that modify state or perform I/O operations.

- Calls the superclass __init__ method: super().__init__(name) (may mutate the instance according to parent implementation).
- Sets instance attribute self.calls to 0 (modifies object state).

### Usage Examples

#### Instantiate an object of the class to ensure parent initialization and reset call counter

```python
obj = ClassUnderTest('worker-1')
```

Creates a new instance, invokes the parent class initializer with 'worker-1', and sets obj.calls to 0.

### Complexity

O(1) time and O(1) space — performs a constant number of operations and sets a single attribute.

### Related Functions

- `__init__ (superclass)` - Called by this method; superclass initialization logic will run before this method sets self.calls.

### Notes

- No validation is performed on the name parameter in this method; any required validation must be implemented in this class or the superclass.
- Exceptions from the superclass __init__ (if any) will propagate to the caller; this method does not catch exceptions.

---



#### async 

![Type: Async](https://img.shields.io/badge/Type-Async-blue)

### Signature

```python
async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]
```

### Description

This async method increments an instance counter (self.calls), raises a RuntimeError on the first invocation, and otherwise returns a dict containing success status and call metadata.


When awaited, the method increases the instance attribute self.calls by one. If the incremented value equals 1 (i.e., this is the first call on the instance), it raises a RuntimeError with message "transient failure". For subsequent calls (self.calls != 1) it returns a dictionary with keys: 'success' set to True, 'agent' set to self.name, 'task' set to the provided task argument, and 'calls' set to the current self.calls value. No other I/O, external calls, or computations occur.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `self` | `` | ✅ | The instance on which the method is called; used for reading and mutating instance state (specifically self.calls and reading self.name).
 |
| `task` | `str` | ✅ | A string identifying the task; the value is returned verbatim in the result dictionary under the 'task' key.
<br>**Constraints:** No validation performed in this method; any string is accepted |
| `context` | `AgentContext` | ✅ | An AgentContext object passed to the method but not read or used by this implementation.
<br>**Constraints:** This implementation does not inspect or mutate context |

### Returns

**Type:** `Dict[str, Any]`

On successful invocation (not the first call), returns a dictionary with keys: 'success' (True), 'agent' (self.name), 'task' (the task argument), and 'calls' (the current value of self.calls).


**Possible Values:**

- {'success': True, 'agent': <self.name>, 'task': <task>, 'calls': <int>}
- Raises RuntimeError on first call instead of returning

### Raises

| Exception | Condition |
| --- | --- |
| `RuntimeError` | Raised when self.calls equals 1 after incrementing (i.e., on the first invocation for this instance); message is 'transient failure'. |

### Side Effects

> ❗ **IMPORTANT**
> This function has side effects that modify state or perform I/O operations.

- Increments/modifies instance attribute self.calls

### Usage Examples

#### Demonstrate first-call failure and subsequent success

```python
await agent.execute('do-something', context)  # first call: raises RuntimeError
await agent.execute('do-something', context)  # second call: returns result dict
```

On the first awaited call this method raises RuntimeError('transient failure'); calling it again (on the same instance) returns a dict with success=True and the calls counter.

### Complexity

O(1) time and O(1) additional space

### Related Functions

- `__init__` - Likely initializes self.calls and self.name used by this method (not shown in this snippet)

### Notes

- The context parameter is accepted but not used in this implementation.
- The method depends on instance attributes self.calls and self.name; ensure they are initialized before calling.
- The transient failure pattern (raising on first call) is explicit in this code and not configurable here.

---



#### __init__

![Type: Sync](https://img.shields.io/badge/Type-Sync-green)

### Signature

```python
def __init__(self, name: str) -> None
```

### Description

Initializes the instance by delegating construction to the superclass with the provided name and initializing an instance attribute calls to 0.


This constructor calls the superclass __init__ method with the name parameter, then sets an instance attribute self.calls to the integer 0. There is no return value. No validation or other logic is performed.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | `str` | ✅ | A string passed through to the superclass constructor (used by the superclass).
<br>**Constraints:** No constraints are enforced in this implementation; any value of type str is accepted as-is. |

### Returns

**Type:** `None`

Constructors in Python return None; this method does not return any value explicitly.


**Possible Values:**

- None

### Side Effects

> ❗ **IMPORTANT**
> This function has side effects that modify state or perform I/O operations.

- Calls the superclass __init__ method (super().__init__(name))
- Sets/modifies the instance attribute self.calls to 0

### Usage Examples

#### Instantiate an object of a subclass that defines this __init__ to initialize name and reset call counter

```python
instance = SubclassName('example_name')
```

Demonstrates calling the constructor: it delegates to the superclass with 'example_name' and sets instance.calls to 0.

### Complexity

Time complexity: O(1) — performs a constant number of operations (one super call and one assignment). Space complexity: O(1) — uses constant additional space for the attribute assignment.

### Related Functions

- `__init__ (superclass)` - Called by this method to perform superclass initialization with the provided name parameter

### Notes

- No validation or error handling is present; any exceptions raised would originate from the superclass __init__ call.
- This method mutates instance state by setting self.calls; that is the only state change defined here.

---



#### async 

![Type: Async](https://img.shields.io/badge/Type-Async-blue)

### Signature

```python
async def execute(self, task: str, context: AgentContext) -> Dict[str, Any]
```

### Description

Increments an instance counter (self.calls) by one and then unconditionally raises RuntimeError("forced failure").


This asynchronous method performs two operations in sequence: it increments the instance attribute self.calls by 1, and immediately raises a RuntimeError with the message "forced failure". There is no return value because the exception is raised every time the method is invoked; normal completion/return does not occur.

### Parameters

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `self` | `implicit instance reference` | ✅ | Reference to the instance on which the method is called; used to access and modify the self.calls attribute.
 |
| `task` | `str` | ✅ | Task identifier or description passed to the method (not used by the implementation).
 |
| `context` | `AgentContext` | ✅ | Context object for the agent (not used by the implementation).
 |

### Returns

**Type:** `Dict[str, Any]`

The function does not return normally. It always raises a RuntimeError before any value can be returned.


**Possible Values:**

- Never returns a value; always raises RuntimeError("forced failure")

### Raises

| Exception | Condition |
| --- | --- |
| `RuntimeError` | Always raised unconditionally at the end of the method with the message "forced failure". |

### Side Effects

> ❗ **IMPORTANT**
> This function has side effects that modify state or perform I/O operations.

- Increments the instance attribute self.calls by 1 (mutates object state)

### Usage Examples

#### Testing that the orchestrator increments call count and signals failure

```python
await instance.execute('some_task', some_context)
```

Demonstrates that calling the async execute method will increment instance.calls and then raise RuntimeError.

### Complexity

O(1) time complexity and O(1) space complexity: performs a single attribute increment and raises an exception.

### Related Functions

- `N/A` - No related functions are visible in the provided implementation.

### Notes

- The parameters task and context are accepted but not used in the implementation.
- Because the method always raises, callers must handle RuntimeError to avoid unhandled exceptions.
- This method is asynchronous (defined with async def) but contains no await expressions; it still must be awaited by callers.

---



#### test_parallel_swarm_executes_all_sub_agents

![Type: Async](https://img.shields.io/badge/Type-Async-blue)

### Signature

```python
async def test_parallel_swarm_executes_all_sub_agents() -> None
```

### Description

Async pytest test that builds a SwarmOrchestrator with 12 EchoWorker sub-agents, runs 'parallel-task' and asserts all agents succeeded in the returned report.


The test creates a SwarmOrchestrator instance configured with a parallel strategy and max_concurrency of 6. It then creates a list of 12 EchoWorker instances named worker_0 through worker_11 and adds them to the orchestrator via add_sub_agents. The test awaits orchestrator.execute_swarm with the task id 'parallel-task' and an AgentContext(session_id='parallel'), stores the returned report, and asserts that the report indicates success, that total_agents equals 12, successful_agents equals 12, failed_agents equals 0, and that every entry in report['results'] has result['success'] is True. If any assertion fails, an AssertionError will be raised by the test framework.

### Returns

**Type:** `None`

This test function does not return a value; it completes successfully if all assertions pass or raises AssertionError on failure.


**Possible Values:**

- None (function completes without returning a value)
- Raises AssertionError if one or more assertions fail

### Raises

| Exception | Condition |
| --- | --- |
| `AssertionError` | Raised when any of the assert statements evaluating the contents of report or counts (success, total_agents, successful_agents, failed_agents, results) fail. |

### Side Effects

> ❗ **IMPORTANT**
> This function has side effects that modify state or perform I/O operations.

- Constructs SwarmOrchestrator and EchoWorker objects (object instantiation)
- Mutates orchestrator internal state by calling orchestrator.add_sub_agents(workers)
- Invokes an asynchronous operation orchestrator.execute_swarm(...) which may perform external or internal side effects (the test itself awaits this call)

### Usage Examples

#### Run as an async pytest test to verify parallel swarm execution

```python
await test_parallel_swarm_executes_all_sub_agents()
```

Demonstrates how the test sets up an orchestrator with 12 workers and asserts that execute_swarm reports all agents succeeded.

### Complexity

Time complexity O(n) with respect to the number of workers for list creation and final assertions (n = 12 in this test); overall runtime also depends on orchestrator.execute_swarm's asynchronous execution. Space complexity O(n) to hold the workers list and the results in the report.

### Related Functions

- `SwarmOrchestrator.add_sub_agents` - Called by this test to register sub-agents with the orchestrator
- `SwarmOrchestrator.execute_swarm` - Called (awaited) by this test to execute the swarm task and produce the report that the test asserts on
- `EchoWorker` - Instantiated in this test to create the sub-agents that are added to the orchestrator
- `AgentContext` - Used to construct the context passed into execute_swarm

### Notes

- This is a test function intended to be run by an async-capable test runner (e.g., pytest with asyncio support).
- The test assumes orchestrator.execute_swarm returns a dict with keys: 'success', 'total_agents', 'successful_agents', 'failed_agents', and 'results'. These assumptions are checked via assertions.
- Any exceptions raised inside orchestrator.execute_swarm or from object constructors will propagate and fail the test; only AssertionError is explicitly raised by the test itself.
- The exact behavior and side effects of execute_swarm are not visible in this test; the test only awaits and inspects its returned report.

---



#### test_target_agents_and_sub_task_overrides

![Type: Async](https://img.shields.io/badge/Type-Async-blue)

### Signature

```python
async def test_target_agents_and_sub_task_overrides() -> None
```

### Description

Asynchronous pytest that verifies executing a swarm with a targeted agent and per-agent sub-task overrides runs only the target and applies its override.


The test creates a SwarmOrchestrator and two EchoWorker instances, registers both workers as sub-agents on the orchestrator, and then awaits orchestrator.execute_swarm with: a default task name, an AgentContext(session_id="targeted"), a target_agents list including only 'worker_a', and a sub_tasks mapping that provides custom sub-task names for both workers. It then asserts that the returned report indicates only one agent ran, that the run corresponds to 'worker_a', and that the output task for that agent equals the custom task provided for 'worker_a'. Finally it asserts that worker_a was invoked exactly once and worker_b was not invoked.

### Returns

**Type:** `None`

This test function does not return a value; it relies on assertions to validate behavior.


**Possible Values:**

- None (implicit)

### Raises

| Exception | Condition |
| --- | --- |
| `AssertionError` | Raised when any of the assert checks fail (e.g., report contents or worker call counts differ from expectations). |

### Side Effects

> ❗ **IMPORTANT**
> This function has side effects that modify state or perform I/O operations.

- Creates and mutates in-memory objects: instantiates SwarmOrchestrator and EchoWorker objects.
- Calls SwarmOrchestrator.add_sub_agents(...) which mutates the orchestrator's internal state by registering sub-agents.
- Awaits and invokes SwarmOrchestrator.execute_swarm(...), which (as observed by assertions) causes worker invocations and mutation of worker call counters (worker_a.calls and worker_b.calls).

### Usage Examples

#### Test that only a targeted agent runs and receives its sub-task override

```python
await test_target_agents_and_sub_task_overrides()
```

Demonstrates constructing an orchestrator and two workers, registering them, executing the swarm targeted at one worker with per-agent sub_task overrides, and asserting expected report structure and worker invocation counts.

### Complexity

Time complexity depends on the number of registered sub-agents and the orchestration implementation; for this test the observable operations scale with the number of sub-agents (O(n) time). Space complexity is O(n) for the report and auxiliary data proportional to the number of agents.

### Related Functions

- `SwarmOrchestrator.execute_swarm` - Called by this test to perform the swarm execution being validated
- `SwarmOrchestrator.add_sub_agents` - Called by this test to register sub-agents on the orchestrator prior to execution
- `EchoWorker` - Worker implementation used in the test; its call counters are checked to verify invocation behavior

### Notes

- This is a pytest-style async test function (name begins with test_) that uses assert statements for validation.
- The function itself contains no explicit try/except or raise statements besides assertions.
- Behavior beyond what is visible (e.g., network calls inside execute_swarm) is not documented here because implementation of execute_swarm is not shown in this snippet.

---



#### test_retry_policy_recovers_flaky_worker

![Type: Async](https://img.shields.io/badge/Type-Async-blue)

### Signature

```python
async def test_retry_policy_recovers_flaky_worker() -> None
```

### Description

Test coroutine that runs a FlakyWorker under a SwarmOrchestrator with a retry policy and asserts the orchestrator recovers the worker by retrying once.


The coroutine creates a SwarmOrchestrator instance configured with a single allowed sub-agent retry and a sequential strategy. It then creates a FlakyWorker instance, registers it with the orchestrator using add_sub_agent, and awaits orchestrator.execute_swarm with a task name 'retry-task' and an AgentContext(session_id='retry'). After execution it asserts that the returned report indicates overall success, that the first result is successful and was attempted twice, and that the FlakyWorker was invoked twice. The function contains no explicit return statement (returns None when awaited).

### Returns

**Type:** `None`

This async test coroutine returns None when awaited; it signals test success by completing without assertion failures.


**Possible Values:**

- None (completes successfully)
- Raises AssertionError if any assert fails

### Raises

| Exception | Condition |
| --- | --- |
| `AssertionError` | If any of the assert statements about report['success'], report['results'][0]['success'], report['results'][0]['attempts'], or flaky.calls do not hold. |

### Side Effects

> ❗ **IMPORTANT**
> This function has side effects that modify state or perform I/O operations.

- Constructs a SwarmOrchestrator instance (calls its constructor)
- Constructs a FlakyWorker instance (calls its constructor)
- Calls orchestrator.add_sub_agent(flaky) which mutates the orchestrator's internal state by registering a sub-agent
- Awaits orchestrator.execute_swarm(...), invoking orchestrator runtime behavior (may perform tasks, retries, and modify internal state or produce external effects depending on implementation)
- Constructs an AgentContext(session_id='retry')

### Usage Examples

#### Run as part of a pytest test suite

```python
pytest -k test_retry_policy_recovers_flaky_worker
```

Demonstrates that the orchestrator's retry policy causes a flaky worker to be retried once and eventually succeed; the test passes when assertions hold.

#### Manually awaiting in an async test runner

```python
await test_retry_policy_recovers_flaky_worker()
```

Shows how the coroutine can be awaited directly in an async test context (e.g., pytest-asyncio).

### Complexity

O(1) time and O(1) space with respect to this test's visible operations (the function performs a fixed number of constructor calls, one add_sub_agent call, one execute_swarm call, and a few assertions). Actual complexity may depend on implementations of SwarmOrchestrator.execute_swarm and FlakyWorker.

### Related Functions

- `SwarmOrchestrator` - Constructed and used by this test; execute_swarm and add_sub_agent methods are invoked.
- `FlakyWorker` - Constructed and registered as a sub-agent; its observable calls attribute is asserted.
- `AgentContext` - Constructed to provide context (session_id='retry') passed to execute_swarm.

### Notes

- This is a test coroutine (likely run by an async-capable test runner such as pytest-asyncio).
- The function body is fully visible and described; no behavior beyond the visible calls is asserted.
- Any exceptions other than AssertionError may arise from the called constructors or methods, but those are not explicitly raised in this function.

---



#### test_timeout_marks_sub_agent_failure

![Type: Async](https://img.shields.io/badge/Type-Async-blue)

### Signature

```python
async def test_timeout_marks_sub_agent_failure() -> None
```

### Description

Pytest async test that verifies a SwarmOrchestrator marks a slow sub-agent as failed when it exceeds a very short sub-agent timeout.


The test instantiates a SwarmOrchestrator named 'orchestrator' with configuration options sub_agent_timeout set to 0.01 and sub_agent_retries set to 0. It then adds a single EchoWorker sub-agent named 'slow_worker' configured to delay 0.05 seconds. The test awaits orchestrator.execute_swarm with task id 'timeout-task' and an AgentContext whose session_id is 'timeout'. After awaiting, it inspects the returned report (a mapping/dictionary), extracts the first result, and performs assertions that: report['success'] is False, report['failed_agents'] equals 1, the individual result's 'success' is False, result['timed_out'] is True, and the result['error'] string contains 'Timed out after'. There is no explicit return statement so the coroutine returns None when the test completes successfully.

### Returns

**Type:** `None`

The coroutine completes without returning a value; when awaited by the test runner it will either finish normally (implicitly returning None) or raise an AssertionError if any assertion fails.


**Possible Values:**

- None (on success)
- Raises AssertionError (if any assertion fails)
- Raises any exception propagated from SwarmOrchestrator.execute_swarm or constructors (if they raise)

### Raises

| Exception | Condition |
| --- | --- |
| `AssertionError` | Raised if any of the assert statements fail (i.e., the observed report does not match expected timeout/failure properties). |

### Side Effects

> ❗ **IMPORTANT**
> This function has side effects that modify state or perform I/O operations.

- Instantiates SwarmOrchestrator object (allocates in-memory state)
- Calls SwarmOrchestrator.add_sub_agent, which mutates the orchestrator's internal state by registering a sub-agent
- Constructs an EchoWorker instance (allocates in-memory state)
- Awaits SwarmOrchestrator.execute_swarm, which may perform asynchronous operations internal to the orchestrator (external effects depend on its implementation and are not visible in this test code)

### Usage Examples

#### Use in an async pytest test suite to verify timeout behavior of SwarmOrchestrator

```python
async def test_timeout_marks_sub_agent_failure():
    # (body as shown in source) 
```

Demonstrates constructing an orchestrator with a short sub-agent timeout, adding a slow worker, executing the swarm, and asserting the report indicates a timeout-caused failure.

### Complexity

O(1) time and space complexity for the test function itself (constant-time operations and fixed-size data). The awaited execute_swarm call's complexity depends on SwarmOrchestrator implementation and is not visible here.

### Related Functions

- `SwarmOrchestrator.execute_swarm` - Called by this test (awaited); the test verifies observable behavior of this function.
- `SwarmOrchestrator.add_sub_agent` - Called by this test to register a sub-agent on the orchestrator instance.
- `EchoWorker` - Constructed and added as the slow sub-agent whose delay triggers the timeout scenario.

### Notes

- This is a test function intended to be run by an async-capable test runner (e.g., pytest with pytest-asyncio).
- The precise behavior (e.g., whether execute_swarm performs network or concurrency operations) is not visible here; the test only inspects the returned report dictionary.
- The test relies on specific keys and structure in the returned report: 'success', 'failed_agents', and a 'results' list containing dicts with 'success', 'timed_out', and 'error' keys.

---



#### async 

![Type: Async](https://img.shields.io/badge/Type-Async-blue)

### Signature

```python
async def test_fail_fast_sequential_skips_remaining_agents():
```

### Description

Async pytest test verifying a SEQUENTIAL SwarmOrchestrator with fail_fast=True stops executing remaining agents after one fails and records skipped agents.


The test constructs a SwarmOrchestrator configured with sequential strategy and fail-fast behavior, creates two worker agents (one that always fails and one echo worker expected to be skipped), registers both as sub-agents on the orchestrator, runs execute_swarm asynchronously with a task name and AgentContext, and then asserts the returned report reflects a failure overall, contains two agents, records the failing agent's failure, records that the second agent had zero attempts and an error message indicating it was skipped due to the fail_fast policy, and confirms the skipped worker was not invoked (calls == 0).

### Returns

**Type:** `None`

This test function does not return a value; it uses assertions to validate behavior. If assertions pass, the test completes normally (returns None). If assertions fail, an AssertionError is raised.


**Possible Values:**

- None (on success)
- Raises AssertionError (on test failure)

### Raises

| Exception | Condition |
| --- | --- |
| `AssertionError` | Any of the inline assert statements fails (e.g., report indicates success, wrong total_agents, unexpected agent names, unexpected attempts, or wrong error message). |

### Side Effects

> ❗ **IMPORTANT**
> This function has side effects that modify state or perform I/O operations.

- Instantiates SwarmOrchestrator, AlwaysFailWorker, and EchoWorker objects
- Mutates orchestrator state by calling orchestrator.add_sub_agent(...) to register sub-agents
- Invokes an asynchronous operation orchestrator.execute_swarm(...), which may trigger internal orchestrator/worker behavior and mutate their internal state (e.g., worker call counters)
- Performs assertions that may raise AssertionError

### Usage Examples

#### Run this test as part of the test suite to assert fail-fast behavior in sequential orchestration

```python
await test_fail_fast_sequential_skips_remaining_agents()  # executed by pytest-asyncio or equivalent test runner
```

Demonstrates invoking the async test function; in practice, a test runner like pytest with an asyncio plugin will discover and run this test.

### Complexity

O(1) time and space complexity with respect to number of operations in the test (constant work: creating two workers, registering them, and executing a single swarm run). Note: actual orchestrator.execute_swarm complexity depends on its implementation but is not visible here.

### Related Functions

- `SwarmOrchestrator.add_sub_agent` - Called by this test to register sub-agents on the orchestrator
- `SwarmOrchestrator.execute_swarm` - Called (awaited) by this test to run the swarm and produce a report that's asserted against
- `AlwaysFailWorker` - Instantiated and used as the failing agent under test
- `EchoWorker` - Instantiated and used as the agent expected to be skipped
- `AgentContext` - Instantiated and passed into execute_swarm as context for the task

### Notes

- This is a pytest-style async test function; it relies on the behavior and return structure of SwarmOrchestrator.execute_swarm and the worker implementations (AlwaysFailWorker and EchoWorker).
- The test asserts specific keys and values in the returned report dictionary (e.g., 'success', 'total_agents', 'results' structure). Those shapes are assumed from the test and must match the orchestrator's implementation.
- Do not assume the internal behavior of execute_swarm beyond what's asserted here; the implementation is not visible in this snippet.

---



#### test_execute_mass_swarm_runs_multiple_operations

![Type: Async](https://img.shields.io/badge/Type-Async-blue)

### Signature

```python
async def test_execute_mass_swarm_runs_multiple_operations() -> None
```

### Description

Test that execute_mass_swarm returns a report indicating four successful operations when run with four tasks in parallel against three EchoWorker sub-agents.


The test creates a SwarmOrchestrator instance configured with max_task_concurrency=3 and max_concurrency=4, registers three EchoWorker instances as sub-agents, prepares an AgentContext with session_id 'mass', and awaits the orchestrator.execute_mass_swarm call with a list of four task identifiers and parallel_tasks=True. After awaiting the call it assigns the result to 'report' and performs a series of assertions verifying: report['success'] is True, total/successful/failed task counts in the report equal 4/4/0 respectively, the report contains four per-operation entries, each operation reports total_agents == 3, and the context.state['swarm_history'] contains four entries. The function does not return a value explicitly (returns None) and will raise AssertionError if any assertion fails.

### Returns

**Type:** `None`

The test does not return a value; it implicitly returns None. Success is indicated by completion without raising an AssertionError.


**Possible Values:**

- None (on success)
- Raises AssertionError if any assertion fails

### Raises

| Exception | Condition |
| --- | --- |
| `AssertionError` | Raised when any of the assert statements about the report contents or the context.state['swarm_history'] length fail |
| `Exception` | Any exception raised by called constructors or orchestrator.execute_mass_swarm will propagate (e.g., from SwarmOrchestrator, EchoWorker, AgentContext, or execute_mass_swarm) |

### Side Effects

> ❗ **IMPORTANT**
> This function has side effects that modify state or perform I/O operations.

- Mutates the SwarmOrchestrator instance by calling add_sub_agents (registers three EchoWorker agents)
- Calls orchestrator.execute_mass_swarm which may mutate the provided AgentContext (the test checks context.state['swarm_history'])

### Usage Examples

#### Run the test to verify execute_mass_swarm returns four successful operations with three agents each

```python
await test_execute_mass_swarm_runs_multiple_operations()
```

Demonstrates creating an orchestrator, adding three EchoWorker agents, executing four tasks in parallel, and asserting the expected report and context state changes.

### Complexity

This test's local operations are O(1), but the total runtime is dominated by the asynchronous call to orchestrator.execute_mass_swarm; the complexity depends on that implementation.

### Related Functions

- `SwarmOrchestrator.execute_mass_swarm` - Called by this test; the test asserts properties of its returned report and its effects on the provided AgentContext
- `SwarmOrchestrator.add_sub_agents` - Called to register agents on the orchestrator prior to executing the swarm
- `EchoWorker` - Instantiated and added as sub-agents to the orchestrator
- `AgentContext` - Instantiated and passed into execute_mass_swarm; its state is inspected after execution

### Notes

- This is a test function (likely used with an async-capable test runner such as pytest-asyncio).
- Behavior and side effects beyond the visible mutations (e.g., what execute_mass_swarm does internally) are not described here because their implementations are not shown in the provided snippet.
- The test relies on execute_mass_swarm populating report keys: 'success', 'total_tasks', 'successful_tasks', 'failed_tasks', and 'operations', and on context.state['swarm_history'] being updated.

---


