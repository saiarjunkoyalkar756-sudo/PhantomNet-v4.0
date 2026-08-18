# Runtime Security Posture and Readiness

## Purpose

PhantomNet’s shared health layer now reports a **runtime security posture** alongside dependency readiness. The posture is an operator-facing safety summary: it reports enabled, disabled, degraded, ready, and not-ready controls without returning a secret value, connection string, HMAC key, AWS credential, or endpoint credential.

> A process can be live while not ready to provide governed protection. Active-mode readiness is successful only when its declared dependencies are healthy and no explicitly enabled security control is misconfigured.

## Core controls

| Control | Ready condition | Non-ready condition |
|---|---|---|
| Safe mode | `PHANTOMNET_SAFE_MODE=true` intentionally disables real integrations | Not applicable; safe mode reports `readiness: safe_mode` rather than active readiness |
| Containment execution audit | Both containment HMAC key and HMAC key ID are configured | The audit posture is degraded; it blocks any enabled response adapter |
| Endpoint containment | Adapter enabled, HMAC audit available, tenant allowlist non-empty, asset allowlist non-empty | Missing HMAC material or either allowlist |
| AWS Security Group containment | Adapter enabled, HMAC audit available, valid tenant-to-group mapping, region/account/CIDR allowlists populated | Invalid JSON, malformed mapping, missing allowlist, missing audit material, or LocalStack endpoint override in production/staging |
| Graph backend | Neo4j backend with a configured password, or explicit ephemeral memory mode | Unsupported backend or Neo4j mode without a password |

A disabled response adapter is an intentional security state and does not block readiness. An enabled but incomplete adapter is a fail-closed misconfiguration: the shared `/ready` route returns a not-ready response even if database, Redis, Kafka, or Neo4j connectivity is otherwise healthy.

## Health response shape

The standard `/health` and `/ready` routes include a `security_posture` object with an overall status, a list of blocking controls, and individual control records. Values are deliberately limited to statuses, reasons, backend names, and non-sensitive allowlist counts.

```json
{
  "security_posture": {
    "status": "not_ready",
    "environment": "production",
    "safe_mode": false,
    "blocking_controls": ["aws_security_group_containment"],
    "controls": {
      "aws_security_group_containment": {
        "status": "not_ready",
        "reason": "missing_hmac_execution_audit"
      }
    }
  }
}
```

## Operator configuration

Use the canonical `PHANTOMNET_SAFE_MODE` environment variable. The legacy `SAFE_MODE` setting remains a compatibility fallback for typed settings only. Keep safe mode enabled until a non-production validation confirms each dependency and adapter boundary.

For a real AWS deployment, `PHANTOMNET_AWS_ENDPOINT_URL` must remain unset. It exists only for explicitly isolated LocalStack tests; a production or staging posture with this override configured is deliberately not ready. All real credentials remain managed by the AWS SDK provider chain and containment HMAC environment variables, never through status output.

## Validation

The core tests verify disabled-by-default posture, HMAC enforcement for enabled AWS containment, strict-environment refusal of test endpoint overrides, invalid tenant-to-Security-Group allowlist refusal, non-secret ready summaries, typed safe-mode alias behavior, and `/ready` failure when a security control blocks operation.
