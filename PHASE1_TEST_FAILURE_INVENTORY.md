# Phase 1 Test Failure Inventory

## Scope

This inventory was created **before any Phase 1 code fixes**. The full suite was executed with:

```bash
python3 -m pytest tests/ phantomnet_agent/tests/ blockchain_layer/test_blockchain.py -vv --tb=long
```

The run collected 98 tests and finished with **68 passed, 19 failed, and 11 errors**. The failure list below preserves the test, exact reported message, trace location, and an initial root-cause category. The category is a triage hypothesis to guide the first repair pass; it is not a reason to weaken or remove any test.

## Summary by category

| Category | Count | Primary area |
|---|---:|---|
| Async/event loop misconfiguration or async interface mismatch | 10 | HTTP, Redis, Kafka, honeypot APIs |
| Hard-coded path or environment assumption | 6 | Blockchain test fixture |
| Test itself is wrong or stale relative to the contract | 8 | Collector fixture, DNS assertion, plugin sandbox constructor |
| Real logic bug | 6 | Redis imports, agent-state coupling, honeypot route behavior |

## Errors

| Test | Exact error | Trace location | Category | Initial interpretation |
|---|---|---|---|---|
| `phantomnet_agent/tests/test_collectors.py::test_process_collector` | `TypeError: Can't instantiate abstract class MockTransport without an implementation for abstract methods 'connect', 'disconnect', 'send_event'` | `phantomnet_agent/tests/test_collectors.py:29` | Test itself is wrong or stale relative to the contract | The test double is missing implementations required by the transport ABC. |
| `phantomnet_agent/tests/test_collectors.py::test_file_collector_periodic_scan` | `TypeError: Can't instantiate abstract class MockTransport without an implementation for abstract methods 'connect', 'disconnect', 'send_event'` | `phantomnet_agent/tests/test_collectors.py:29` | Test itself is wrong or stale relative to the contract | Same incomplete test double. |
| `phantomnet_agent/tests/test_collectors.py::test_network_collector` | `TypeError: Can't instantiate abstract class MockTransport without an implementation for abstract methods 'connect', 'disconnect', 'send_event'` | `phantomnet_agent/tests/test_collectors.py:29` | Test itself is wrong or stale relative to the contract | Same incomplete test double. |
| `phantomnet_agent/tests/test_collectors.py::test_dns_collector` | `TypeError: Can't instantiate abstract class MockTransport without an implementation for abstract methods 'connect', 'disconnect', 'send_event'` | `phantomnet_agent/tests/test_collectors.py:29` | Test itself is wrong or stale relative to the contract | Same incomplete test double. |
| `phantomnet_agent/tests/test_collectors.py::test_log_collector` | `TypeError: Can't instantiate abstract class MockTransport without an implementation for abstract methods 'connect', 'disconnect', 'send_event'` | `phantomnet_agent/tests/test_collectors.py:29` | Test itself is wrong or stale relative to the contract | Same incomplete test double. |
| `blockchain_layer/test_blockchain.py::test_new_blockchain_creates_genesis_block` | `PermissionError: [Errno 13] Permission denied: '/home/joyhark522'` | `blockchain_layer/test_blockchain.py:34` | Hard-coded path or environment assumption | Fixture writes below a developer-specific absolute home directory. |
| `blockchain_layer/test_blockchain.py::test_new_transaction_adds_to_db_session` | `PermissionError: [Errno 13] Permission denied: '/home/joyhark522'` | `blockchain_layer/test_blockchain.py:34` | Hard-coded path or environment assumption | Same fixture path. |
| `blockchain_layer/test_blockchain.py::test_new_block_links_pending_transactions_and_resets` | `PermissionError: [Errno 13] Permission denied: '/home/joyhark522'` | `blockchain_layer/test_blockchain.py:34` | Hard-coded path or environment assumption | Same fixture path. |
| `blockchain_layer/test_blockchain.py::test_proof_of_work_finds_valid_proof` | `PermissionError: [Errno 13] Permission denied: '/home/joyhark522'` | `blockchain_layer/test_blockchain.py:34` | Hard-coded path or environment assumption | Same fixture path. |
| `blockchain_layer/test_blockchain.py::test_is_chain_valid_with_valid_chain` | `PermissionError: [Errno 13] Permission denied: '/home/joyhark522'` | `blockchain_layer/test_blockchain.py:34` | Hard-coded path or environment assumption | Same fixture path. |
| `blockchain_layer/test_blockchain.py::test_is_chain_valid_with_full_transaction` | `PermissionError: [Errno 13] Permission denied: '/home/joyhark522'` | `blockchain_layer/test_blockchain.py:34` | Hard-coded path or environment assumption | Same fixture path. |

## Failures

| Test | Exact error | Trace location | Category | Initial interpretation |
|---|---|---|---|---|
| `phantomnet_agent/tests/test_bus.py::test_http_transport_send_event_success` | `TypeError: HttpTransport.send_event() takes 2 positional arguments but 3 were given` | `phantomnet_agent/tests/test_bus.py:30` | Async/event loop misconfiguration or async interface mismatch | The test calls a topic-plus-event contract while `HttpTransport` exposes only one event argument. |
| `phantomnet_agent/tests/test_bus.py::test_http_transport_send_event_failure` | `TypeError: HttpTransport.send_event() takes 2 positional arguments but 3 were given` | `phantomnet_agent/tests/test_bus.py:58` | Async/event loop misconfiguration or async interface mismatch | Same interface mismatch. |
| `phantomnet_agent/tests/test_bus.py::test_http_transport_receive_commands` | `TypeError: object async_generator can't be used in 'await' expression` | `phantomnet_agent/tests/test_bus.py:70` | Async/event loop misconfiguration or async interface mismatch | The test and implementation disagree on whether the method returns an awaitable or an async iterator. |
| `phantomnet_agent/tests/test_bus.py::test_redis_transport_send_event` | `NameError: name 'get_agent_state' is not defined` | `phantomnet_agent/bus/redis_bus.py:50`, then `:60` | Real logic bug | The connection path references an unimported symbol and masks the transport result. |
| `phantomnet_agent/tests/test_bus.py::test_redis_transport_receive_commands` | `NameError: name 'get_agent_state' is not defined` | `phantomnet_agent/bus/redis_bus.py:50`, then `:60` | Real logic bug | Same missing import and global-state coupling. |
| `phantomnet_agent/tests/test_bus.py::test_kafka_transport_send_event` | `RuntimeError: Agent state has not been initialized. Call initialize_agent_state first.` | `phantomnet_agent/bus/kafka_bus.py:56`; `phantomnet_agent/core/state.py:107` | Real logic bug | Graceful Kafka no-op handling itself raises because optional health reporting requires global agent state. |
| `phantomnet_agent/tests/test_bus.py::test_kafka_transport_receive_commands` | `RuntimeError: Agent state has not been initialized. Call initialize_agent_state first.` | `phantomnet_agent/bus/kafka_bus.py:56`; `phantomnet_agent/core/state.py:107` | Real logic bug | Same optional-state dependency; test patch also did not replace the imported implementation used by the active module. |
| `phantomnet_agent/tests/test_honeypot_service.py::test_create_honeypot` | `TypeError: 'coroutine' object is not iterable` | `backend_api/honeypot_service/main.py:21` | Async/event loop misconfiguration or async interface mismatch | The route iterates `honeypot_manager.list_honeypots()` without awaiting the coroutine. |
| `phantomnet_agent/tests/test_honeypot_service.py::test_list_honeypots` | `fastapi.exceptions.ResponseValidationError: 1 validation errors` | Route response path from `GET /honeypots`; exact inner model mismatch is captured in the pytest log | Async/event loop misconfiguration or async interface mismatch | The endpoint exposes unawaited/asynchronous manager output that does not satisfy its response model. |
| `phantomnet_agent/tests/test_honeypot_service.py::test_stop_honeypot` | `AttributeError: 'coroutine' object has no attribute 'status'` | `backend_api/honeypot_service/main.py:45` | Async/event loop misconfiguration or async interface mismatch | The stop route accesses `.status` on an unawaited coroutine. |
| `phantomnet_agent/tests/test_honeypot_service.py::test_get_honeypot_events` | `assert 200 == 404` | `phantomnet_agent/tests/test_honeypot_service.py` endpoint assertion | Real logic bug | Unknown honeypot lookup incorrectly returns an OK response; manager status is also invoked without awaiting at `main.py:52`. |
| `phantomnet_agent/tests/test_honeypot_service.py::test_ssh_honeypot_interaction_and_metrics` | `assert 'honeypot_sessions_total{honeypot_id="integration_ssh_honeypot",honeypot_type="ssh"} 0.0' in ''` | `phantomnet_agent/tests/test_honeypot_service.py` | Async/event loop misconfiguration or async interface mismatch | The integration test expects metrics from a honeypot interaction but receives an empty metrics payload; fixture/service lifecycle must be made deterministic. |
| `phantomnet_agent/tests/test_network_sensor.py::test_process_dns_packet` | `AssertionError: expected call not found.` Expected entropy `2.5216406363433186`; actual entropy `2.6635327548042547`. | `phantomnet_agent/tests/test_network_sensor.py:42` | Test itself is wrong or stale relative to the contract | The test hard-codes an entropy result that differs from the implementation’s current calculation. Confirm the intended entropy algorithm before changing either side. |
| `phantomnet_agent/tests/test_plugins.py::test_plugin_loader_load_valid_plugin` | `RuntimeError: Agent state has not been initialized. Call initialize_agent_state first.` | `phantomnet_agent/plugins/loader.py:38`; `phantomnet_agent/core/state.py:107` | Real logic bug | Plugin loader cannot be constructed in isolation because it directly reads global agent state. |
| `phantomnet_agent/tests/test_plugins.py::test_plugin_loader_unallowed_permissions` | `RuntimeError: Agent state has not been initialized. Call initialize_agent_state first.` | `phantomnet_agent/plugins/loader.py:38`; `phantomnet_agent/core/state.py:107` | Real logic bug | Same isolation defect prevents the permission test from reaching its assertion. |
| `phantomnet_agent/tests/test_plugins.py::test_plugin_loader_malformed_manifest` | `RuntimeError: Agent state has not been initialized. Call initialize_agent_state first.` | `phantomnet_agent/plugins/loader.py:38`; `phantomnet_agent/core/state.py:107` | Real logic bug | Same isolation defect prevents malformed-manifest handling from being tested. |
| `phantomnet_agent/tests/test_plugins.py::test_plugin_sandbox_fast_function` | `TypeError: PluginSandbox.__init__() missing 1 required positional argument: 'allowed_permissions'` | `phantomnet_agent/tests/test_plugins.py:98` | Test itself is wrong or stale relative to the contract | The test calls an older constructor contract; confirm whether permissions should have a safe default or must be supplied explicitly. |
| `phantomnet_agent/tests/test_plugins.py::test_plugin_sandbox_timeout_function` | `TypeError: PluginSandbox.__init__() missing 1 required positional argument: 'allowed_permissions'` | `phantomnet_agent/tests/test_plugins.py:107` | Test itself is wrong or stale relative to the contract | Same constructor-contract mismatch. |
| `phantomnet_agent/tests/test_plugins.py::test_plugin_sandbox_function_with_exception` | `TypeError: PluginSandbox.__init__() missing 1 required positional argument: 'allowed_permissions'` | `phantomnet_agent/tests/test_plugins.py:117` | Test itself is wrong or stale relative to the contract | Same constructor-contract mismatch. |

## Non-blocking warnings that must not be ignored later

The run also reported repeated attempts to reach `localhost:8000` during test setup, unawaited-honeypot coroutine warnings at `backend_api/honeypot_service/main.py:21` and `:52`, Pydantic deprecation warnings, and a Scapy DNS-field deprecation warning. These are not counted as failures but indicate test isolation and asynchronous lifecycle defects that must be resolved as Phase 1 work proceeds.

## Required repair order

1. Replace the hard-coded blockchain path with a `tmp_path` fixture or an explicitly scoped test environment directory.
2. Establish one transport protocol for `connect`, `disconnect`, `send_event`, and command iteration, then repair all HTTP, Redis, and Kafka implementations and tests against it.
3. Remove optional global-state dependencies from transport and plugin construction, or inject a fully testable state interface.
4. Await all honeypot manager calls and make endpoint responses conform to their declared models.
5. Correct the collector test double, then verify collector behavior.
6. Resolve the DNS entropy contract deliberately and align test/implementation only after documenting the chosen algorithm.
7. Repair plugin-loader and plugin-sandbox contracts without reducing permission controls.

No test should be removed merely to improve the count. Each repair must include an isolated success and failure test; response changes must include verification, rollback, and audit tests where applicable.
