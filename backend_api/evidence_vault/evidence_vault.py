"""Compatibility facade for tenant-scoped, read-only evidence storage.

The prior process-local unscoped vault has been retired. Callers must supply a tenant and the
source provenance required by the durable Phase 4 evidence integration layer.
"""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from typing import Any

from backend_api.evidence_vault.integration import EvidenceIntegrationService, EvidenceSourceKind
from phantomnet_core.contracts import IntegratedEvidenceRecord


class EvidenceVault:
    """Store and retrieve only tenant-owned, read-only integrated evidence."""

    def __init__(self, integration: EvidenceIntegrationService | None = None) -> None:
        self._integration = integration or EvidenceIntegrationService()

    async def store_evidence(
        self,
        data: str,
        source: str,
        tags: list[str],
        filename: str | None = None,
        *,
        tenant_id: str,
        source_kind: EvidenceSourceKind,
        source_record_id: str | None = None,
        provenance: Mapping[str, Any] | None = None,
    ) -> str:
        """Store bounded source evidence with mandatory tenant scope and read-only provenance."""
        content_hash = sha256(data.encode("utf-8")).hexdigest()
        record = IntegratedEvidenceRecord(
            tenant_id=tenant_id,
            source_kind=source_kind,
            source_name=source,
            source_record_id=source_record_id or filename or content_hash,
            payload={"content": data, "filename": filename, "content_sha256": content_hash},
            tags=tags,
            provenance={**dict(provenance or {}), "adapter": "evidence-vault", "read_only": True},
        )
        outcome = await self._integration.ingest(record)
        return outcome.record.evidence_id

    async def retrieve_evidence(self, evidence_id: str, *, tenant_id: str) -> dict[str, Any] | None:
        """Retrieve one evidence record only if it belongs to the requested tenant."""
        try:
            return (await self._integration.get_for_tenant(tenant_id, evidence_id)).model_dump(mode="json")
        except LookupError:
            return None

    async def search_evidence(
        self,
        query: str,
        *,
        tenant_id: str,
        tags: list[str] | None = None,
        source_kind: EvidenceSourceKind | None = None,
    ) -> list[dict[str, Any]]:
        """Search tenant-owned evidence metadata only; this method does not inspect raw evidence content."""
        records = await self._integration.list_for_tenant(tenant_id, source_kind=source_kind)
        normalized_query = query.casefold().strip()
        required_tags = {tag.casefold() for tag in tags or []}
        results: list[dict[str, Any]] = []
        for record in records:
            searchable = " ".join(
                [record.evidence_id, record.source_name, record.source_kind, record.source_record_id, *record.tags]
            ).casefold()
            record_tags = {tag.casefold() for tag in record.tags}
            if normalized_query and normalized_query not in searchable:
                continue
            if required_tags and not required_tags.issubset(record_tags):
                continue
            results.append(record.model_dump(mode="json"))
        return results


evidence_vault = EvidenceVault()
