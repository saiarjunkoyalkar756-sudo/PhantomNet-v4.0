# Legacy Auto-Response Engine Compatibility Boundary

This package no longer exposes automated response execution. Its retained ASGI entry point is a **fail-closed `410` compatibility boundary** for legacy callers; it does not execute playbooks, issue agent commands, or invoke security controls.

High-impact response actions must use the supported governed containment lifecycle in `backend_api/soar_engine/governed_containment.py`. That lifecycle preserves the required request, human-approval, HMAC-signed audit, controlled-adapter execution, verification, and rollback controls.

The legacy package is intentionally not included in the root development Compose topology or the hardened self-hosted reference topology.
