# Endpoint Command Signing and Provisioning Protocol

## Status and scope

PhantomNet’s governed agent-command producer now uses a detached **RSA-PSS/SHA-256** signature over a canonical `phantomnet.agent-command.v1` envelope. The producer signs only after an authenticated, capability-checked request is constructed and before the existing audit-first broker publish sequence begins. The endpoint agent refuses to reach any command handler unless it can verify the complete original broker envelope against an operator-provisioned trusted certificate or public key.

> This protocol applies to endpoint commands only. It does not replace signed telemetry ingestion, user authentication, containment approval, HMAC audit records, adapter verification, or rollback controls.

## Required deployment inputs

| Component | Required input | Handling requirement |
|---|---|---|
| Governed command producer | `PHANTOMNET_AGENT_COMMAND_SIGNING_PRIVATE_KEY` | PEM-encoded RSA private key injected only at deployment/runtime. It must never be placed in source control, logs, test fixtures, or API responses. |
| Endpoint agent | `PHANTOMNET_AGENT_COMMAND_TRUSTED_CERT_PATH` | Absolute path to the corresponding PEM public key or X.509 certificate, mounted with read-only permissions. |
| Broker envelope | `signature` and `signature_algorithm` | The algorithm must be `RSA-PSS-SHA256`; the complete original envelope is retained until verification. |

The canonical signing payload binds the domain, `tenant_id`, `target_agent_id`, `command_type`, `arguments`, `task_id`, `issued_by`, and `issued_at`. Changing any bound value invalidates the signature.

## Fail-closed behavior

The command producer returns an unavailable outcome without publishing an audit intent or command if its signing key is missing, malformed, or unusable. When signing succeeds, the producer publishes the request audit event before the signed command envelope. The endpoint rejects the command before any executor handler when the signature is missing, malformed, unsupported, altered, unverifiable, or its trusted certificate path is absent.

This removes the former environment-controlled unsigned-command fallback. A deployment that has not completed key provisioning will therefore not dispatch executable endpoint commands. That reduction in availability is deliberate and safer than accepting unauthenticated broker messages.

## Mandatory trust-chain rotation

Previously tracked endpoint certificate and private-key artifacts were removed from source control. Because any private key that was committed must be treated as exposed, operators **must not reuse it**. Generate a fresh non-production or production-specific trust chain outside the repository, store private material in an approved secret manager or host-mounted secret, and distribute only the corresponding trusted public certificate/key to endpoint agents.

The included certificate-generation utility is a controlled bootstrap aid only. Its outputs are ignored by Git. Before a production rollout, operators must review certificate ownership, rotation period, revocation procedure, filesystem permissions, and separation of the command-signing private key from CA or endpoint identity keys.

## Controlled-device validation gate

A qualified operator should capture secret-free evidence of the following in an isolated environment before claiming endpoint command validation:

1. A newly generated, non-repository signing key is injected into the producer and the matching public certificate/key is mounted on one enrolled agent.
2. An authorized command produces an audit intent before a signed broker message and the agent verifies it before invoking an allowed handler.
3. A modified bound field, malformed signature, missing signature, absent trusted certificate, and mismatched public key each produce a rejection with no handler invocation.
4. Private key material, certificate paths, command arguments containing secrets, and broker credentials are absent from the captured evidence.
5. The test command is non-destructive, and any endpoint action remains within the existing approval, audit, verification, and rollback rules.

> **Evidence classification:** the present implementation and isolated regressions are **Class A** evidence. They do not prove device packaging, OS trust-store behavior, certificate rotation in production, broker ACLs, real endpoint execution, or containment effectiveness. Those claims require controlled external-lab evidence.
