# Local Enforcement Adapter

## Purpose

The PhantomNet SOAR local enforcement adapter can apply a **local outbound `iptables` reject rule** for a narrowly constrained sandbox test. It is designed to replace misleading placeholder success responses with a verifiable local action.

The adapter is not a general firewall manager and is not an EDR integration. It deliberately rejects all targets except the RFC 5737 documentation networks: `192.0.2.0/24`, `198.51.100.0/24`, and `203.0.113.0/24`.

## Safe defaults

The default mode is `dry-run`. In this mode, `block_ip` returns a successful planned action but explicitly reports `enforced: false` and `verified: false`; no command is invoked.

Host isolation and process termination remain unavailable until a supported endpoint-management provider is integrated. They return failure rather than falsely reporting containment.

## Controlled local test

A real local rule requires root privileges and both explicit environment settings:

```bash
export PHANTOMNET_LOCAL_ENFORCEMENT_MODE=enabled
export PHANTOMNET_LOCAL_ENFORCEMENT_CONFIRM=I_UNDERSTAND_LOCAL_FIREWALL_CHANGES
```

The adapter then permits only documentation addresses. For example, a local test can apply and verify a rule for `198.51.100.42`, followed immediately by `rollback_block_ip`.

## Verification and rollback

The adapter uses an adapter-owned iptables comment, `phantomnet-local`, and verifies the exact rule using `iptables -C` after applying it. Rollback removes only that exact adapter-owned rule and verifies that it is absent.

Every request is written to `logs/local_enforcement_audit.log`, including mode, target, enforcement status, verification status, rollback status, and a human-readable result.

## Production requirement

Do not use this adapter as proof of protection for real assets. Production containment needs dedicated, authenticated provider adapters for the firewall and endpoint-management systems, a target allowlist, approval workflow, idempotency controls, outcome verification from the provider, and a rollback policy.
