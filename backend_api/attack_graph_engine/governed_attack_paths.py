"""Governed, evidence-backed attack-path analysis.

The service accepts only PhantomNet's canonical tenant-owned records, projects them into an
isolated graph per tenant, and performs bounded read-only traversal. It deliberately contains no
response-adapter, containment, playbook-execution, or arbitrary query capability.
"""

from __future__ import annotations

import asyncio
import json
import os
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal, Protocol
from uuid import UUID

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from phantomnet_core.contracts import (
    AlertRecord,
    CaseRecord,
    DetectionRecord,
    HostAssetRecord,
    IntegrityObservation,
)


GraphNodeKind = Literal["asset", "integrity_observation", "detection", "alert", "case", "mitre_technique"]
GraphRelationship = Literal[
    "INTEGRITY_OBSERVED_ON_ASSET",
    "DETECTION_OBSERVED_ON_ASSET",
    "DETECTION_OBSERVED_ON_INTEGRITY",
    "DETECTION_MATCHES_MITRE_TECHNIQUE",
    "ALERT_DERIVED_FROM_DETECTION",
    "CASE_INVESTIGATES_ALERT",
]

MAX_GRAPH_HOPS = 6
MAX_GRAPH_PATHS = 25
MAX_GRAPH_EXPLORATIONS = 5_000

SEVERITY_RISK: dict[str, int] = {
    "informational": 5,
    "low": 20,
    "medium": 45,
    "high": 70,
    "critical": 95,
}


def _canonical_tenant_id(value: str) -> str:
    return str(UUID(value))


def _severity_risk(severity: str) -> int:
    return SEVERITY_RISK.get(severity, SEVERITY_RISK["informational"])


def _deduplicate(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


class AttackGraphNode(BaseModel):
    """A tenant-owned graph node with source-evidence references only."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    node_id: str = Field(min_length=3, max_length=512)
    tenant_id: str
    kind: GraphNodeKind
    label: str = Field(min_length=1, max_length=512)
    risk_score: int = Field(ge=0, le=100)
    evidence_ids: list[str] = Field(default_factory=list, max_length=128)
    attributes: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

    @field_validator("tenant_id")
    @classmethod
    def normalize_tenant(cls, value: str) -> str:
        return _canonical_tenant_id(value)


class AttackGraphEdge(BaseModel):
    """An evidence-bound directional relationship between nodes in one tenant graph."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_node_id: str = Field(min_length=3, max_length=512)
    target_node_id: str = Field(min_length=3, max_length=512)
    relationship: GraphRelationship
    evidence_ids: list[str] = Field(default_factory=list, min_length=1, max_length=128)
    risk_score: int = Field(default=0, ge=0, le=100)


class AttackPathQuery(BaseModel):
    """Strictly bounded graph traversal parameters; no raw Cypher or graph expression is accepted."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_node_id: str = Field(min_length=3, max_length=512)
    target_node_id: str = Field(min_length=3, max_length=512)
    max_hops: int = Field(default=4, ge=1, le=MAX_GRAPH_HOPS)
    max_paths: int = Field(default=10, ge=1, le=MAX_GRAPH_PATHS)

    @model_validator(mode="after")
    def reject_trivial_path(self) -> "AttackPathQuery":
        if self.source_node_id == self.target_node_id:
            raise ValueError("Source and target graph nodes must be different.")
        return self


class AttackPath(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    node_ids: list[str] = Field(min_length=2, max_length=MAX_GRAPH_HOPS + 1)
    edges: list[AttackGraphEdge] = Field(min_length=1, max_length=MAX_GRAPH_HOPS)
    hop_count: int = Field(ge=1, le=MAX_GRAPH_HOPS)
    risk_score: int = Field(ge=0)
    evidence_ids: list[str] = Field(default_factory=list)


class AttackPathAnalysis(BaseModel):
    """Read-only analyst result. It has no action, recommendation, or response-execution field."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str
    source_node_id: str
    target_node_id: str
    paths: list[AttackPath] = Field(default_factory=list, max_length=MAX_GRAPH_PATHS)
    nodes: list[AttackGraphNode] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    analysis_mode: Literal["read_only"] = "read_only"

    @field_validator("tenant_id")
    @classmethod
    def normalize_tenant(cls, value: str) -> str:
        return _canonical_tenant_id(value)


class GraphProjectionResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str
    node_count: int = Field(ge=0)
    edge_count: int = Field(ge=0)
    projected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    analysis_mode: Literal["read_only"] = "read_only"

    @field_validator("tenant_id")
    @classmethod
    def normalize_tenant(cls, value: str) -> str:
        return _canonical_tenant_id(value)


class TenantGraphStore(Protocol):
    async def replace_snapshot(
        self, tenant_id: str, nodes: list[AttackGraphNode], edges: list[AttackGraphEdge]
    ) -> GraphProjectionResult: ...

    async def analyze(self, tenant_id: str, query: AttackPathQuery) -> AttackPathAnalysis: ...


@dataclass(frozen=True)
class _TenantGraphSnapshot:
    graph: nx.DiGraph
    projected_at: datetime


class Neo4jTenantGraphStore:
    """Neo4j-backed tenant graph store using static, parameterized Cypher only.

    The backend is optional so isolated tests do not require a running graph database. It never
    accepts Cypher, labels, relationship types, or tenant identifiers from a graph-query caller.
    """

    _CLEAR_TENANT = "MATCH (node:PhantomNetGraphNode {tenant_id: $tenant_id}) DETACH DELETE node"
    _MERGE_NODES = """
    UNWIND $nodes AS node
    CREATE (:PhantomNetGraphNode {
        tenant_id: $tenant_id,
        node_id: node.node_id,
        kind: node.kind,
        label: node.label,
        risk_score: node.risk_score,
        evidence_ids: node.evidence_ids,
        attributes_json: node.attributes_json
    })
    """
    _MERGE_EDGES = """
    UNWIND $edges AS edge
    MATCH (source:PhantomNetGraphNode {tenant_id: $tenant_id, node_id: edge.source_node_id})
    MATCH (target:PhantomNetGraphNode {tenant_id: $tenant_id, node_id: edge.target_node_id})
    CREATE (source)-[:PHANTOMNET_GRAPH_RELATIONSHIP {
        relationship: edge.relationship,
        evidence_ids: edge.evidence_ids,
        risk_score: edge.risk_score
    }]->(target)
    """
    _FIND_NODES = """
    MATCH (node:PhantomNetGraphNode {tenant_id: $tenant_id})
    WHERE node.node_id IN $node_ids
    RETURN node.node_id AS node_id
    """
    _BOUNDED_PATHS = """
    MATCH path=(source:PhantomNetGraphNode {tenant_id: $tenant_id, node_id: $source_node_id})
        -[:PHANTOMNET_GRAPH_RELATIONSHIP*1..6]->
        (target:PhantomNetGraphNode {tenant_id: $tenant_id, node_id: $target_node_id})
    WHERE length(path) <= $max_hops
    WITH nodes(path) AS graph_nodes, relationships(path) AS graph_edges,
         reduce(node_score = 0, node IN nodes(path) | node_score + node.risk_score)
         + reduce(edge_score = 0, edge IN relationships(path) | edge_score + edge.risk_score) AS risk_score
    RETURN graph_nodes, graph_edges, risk_score
    ORDER BY risk_score DESC, size(graph_edges) ASC
    LIMIT $max_paths
    """

    def __init__(
        self,
        *,
        uri: str | None = None,
        username: str | None = None,
        password: str | None = None,
        driver=None,
    ) -> None:
        if driver is not None:
            self._driver = driver
            return
        configured_uri = uri or os.getenv("NEO4J_URI")
        configured_username = username or os.getenv("NEO4J_USER")
        configured_password = password or os.getenv("NEO4J_PASSWORD")
        if not all((configured_uri, configured_username, configured_password)):
            raise RuntimeError("Neo4j graph store requires NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD.")
        try:
            from neo4j import GraphDatabase
        except ImportError as exc:  # pragma: no cover - depends on deployment extras
            raise RuntimeError("Neo4j graph store requires the optional neo4j package.") from exc
        self._driver = GraphDatabase.driver(configured_uri, auth=(configured_username, configured_password))

    async def replace_snapshot(
        self, tenant_id: str, nodes: list[AttackGraphNode], edges: list[AttackGraphEdge]
    ) -> GraphProjectionResult:
        canonical_tenant = _canonical_tenant_id(tenant_id)
        if any(node.tenant_id != canonical_tenant for node in nodes):
            raise ValueError("Graph projection contains a node owned by a different tenant.")
        node_ids = {node.node_id for node in nodes}
        if any(edge.source_node_id not in node_ids or edge.target_node_id not in node_ids for edge in edges):
            raise ValueError("Graph projection edge references a node outside the tenant snapshot.")
        await asyncio.to_thread(self._replace_snapshot_sync, canonical_tenant, nodes, edges)
        return GraphProjectionResult(tenant_id=canonical_tenant, node_count=len(nodes), edge_count=len(edges))

    def _replace_snapshot_sync(
        self, tenant_id: str, nodes: list[AttackGraphNode], edges: list[AttackGraphEdge]
    ) -> None:
        serialized_nodes = [
            {
                "node_id": node.node_id,
                "kind": node.kind,
                "label": node.label,
                "risk_score": node.risk_score,
                "evidence_ids": node.evidence_ids,
                "attributes_json": json.dumps(node.attributes, sort_keys=True, separators=(",", ":")),
            }
            for node in nodes
        ]
        serialized_edges = [
            {
                "source_node_id": edge.source_node_id,
                "target_node_id": edge.target_node_id,
                "relationship": edge.relationship,
                "evidence_ids": edge.evidence_ids,
                "risk_score": edge.risk_score,
            }
            for edge in edges
        ]
        with self._driver.session() as session:
            with session.begin_transaction() as transaction:
                transaction.run(self._CLEAR_TENANT, tenant_id=tenant_id).consume()
                if serialized_nodes:
                    transaction.run(self._MERGE_NODES, tenant_id=tenant_id, nodes=serialized_nodes).consume()
                if serialized_edges:
                    transaction.run(self._MERGE_EDGES, tenant_id=tenant_id, edges=serialized_edges).consume()
                transaction.commit()

    async def analyze(self, tenant_id: str, query: AttackPathQuery) -> AttackPathAnalysis:
        canonical_tenant = _canonical_tenant_id(tenant_id)
        return await asyncio.to_thread(self._analyze_sync, canonical_tenant, query)

    def _analyze_sync(self, tenant_id: str, query: AttackPathQuery) -> AttackPathAnalysis:
        with self._driver.session() as session:
            known_node_ids = {
                record["node_id"]
                for record in session.run(
                    self._FIND_NODES,
                    tenant_id=tenant_id,
                    node_ids=[query.source_node_id, query.target_node_id],
                )
            }
            if query.source_node_id not in known_node_ids:
                raise LookupError("Source node was not found for the authenticated tenant.")
            if query.target_node_id not in known_node_ids:
                raise LookupError("Target node was not found for the authenticated tenant.")
            records = list(
                session.run(
                    self._BOUNDED_PATHS,
                    tenant_id=tenant_id,
                    source_node_id=query.source_node_id,
                    target_node_id=query.target_node_id,
                    max_hops=query.max_hops,
                    max_paths=query.max_paths,
                )
            )
        paths: list[AttackPath] = []
        result_nodes: dict[str, AttackGraphNode] = {}
        for record in records:
            nodes = [self._node_from_neo4j(dict(node)) for node in record["graph_nodes"]]
            edges = [
                self._edge_from_neo4j(dict(edge), nodes[index].node_id, nodes[index + 1].node_id)
                for index, edge in enumerate(record["graph_edges"])
            ]
            for node in nodes:
                if node.tenant_id != tenant_id:
                    raise RuntimeError("Neo4j returned cross-tenant graph evidence.")
                result_nodes[node.node_id] = node
            paths.append(
                AttackPath(
                    node_ids=[node.node_id for node in nodes],
                    edges=edges,
                    hop_count=len(edges),
                    risk_score=int(record["risk_score"]),
                    evidence_ids=_deduplicate(
                        [evidence_id for node in nodes for evidence_id in node.evidence_ids]
                        + [evidence_id for edge in edges for evidence_id in edge.evidence_ids]
                    ),
                )
            )
        return AttackPathAnalysis(
            tenant_id=tenant_id,
            source_node_id=query.source_node_id,
            target_node_id=query.target_node_id,
            paths=paths,
            nodes=list(result_nodes.values()),
        )

    @staticmethod
    def _node_from_neo4j(properties: dict) -> AttackGraphNode:
        return AttackGraphNode(
            node_id=properties["node_id"],
            tenant_id=properties["tenant_id"],
            kind=properties["kind"],
            label=properties["label"],
            risk_score=int(properties["risk_score"]),
            evidence_ids=list(properties.get("evidence_ids", [])),
            attributes=json.loads(properties.get("attributes_json", "{}")),
        )

    @staticmethod
    def _edge_from_neo4j(properties: dict, source_node_id: str, target_node_id: str) -> AttackGraphEdge:
        return AttackGraphEdge(
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relationship=properties["relationship"],
            evidence_ids=list(properties.get("evidence_ids", [])),
            risk_score=int(properties.get("risk_score", 0)),
        )

    async def close(self) -> None:
        await asyncio.to_thread(self._driver.close)


class InMemoryTenantGraphStore:
    """Testable read-only analysis backend that physically separates graph state by tenant."""

    def __init__(self) -> None:
        self._snapshots: dict[str, _TenantGraphSnapshot] = {}
        self._lock = asyncio.Lock()

    async def replace_snapshot(
        self, tenant_id: str, nodes: list[AttackGraphNode], edges: list[AttackGraphEdge]
    ) -> GraphProjectionResult:
        canonical_tenant = _canonical_tenant_id(tenant_id)
        if any(node.tenant_id != canonical_tenant for node in nodes):
            raise ValueError("Graph projection contains a node owned by a different tenant.")

        next_graph = nx.DiGraph()
        for node in nodes:
            next_graph.add_node(node.node_id, record=node)
        for edge in edges:
            if not next_graph.has_node(edge.source_node_id) or not next_graph.has_node(edge.target_node_id):
                raise ValueError("Graph projection edge references a node outside the tenant snapshot.")
            next_graph.add_edge(edge.source_node_id, edge.target_node_id, record=edge)

        projected_at = datetime.now(timezone.utc)
        async with self._lock:
            self._snapshots[canonical_tenant] = _TenantGraphSnapshot(next_graph, projected_at)
        return GraphProjectionResult(
            tenant_id=canonical_tenant,
            node_count=next_graph.number_of_nodes(),
            edge_count=next_graph.number_of_edges(),
            projected_at=projected_at,
        )

    async def analyze(self, tenant_id: str, query: AttackPathQuery) -> AttackPathAnalysis:
        canonical_tenant = _canonical_tenant_id(tenant_id)
        async with self._lock:
            snapshot = self._snapshots.get(canonical_tenant)
            graph = snapshot.graph.copy() if snapshot is not None else nx.DiGraph()

        if not graph.has_node(query.source_node_id):
            raise LookupError("Source node was not found for the authenticated tenant.")
        if not graph.has_node(query.target_node_id):
            raise LookupError("Target node was not found for the authenticated tenant.")

        paths = _bounded_simple_paths(graph, query)
        path_records = [_path_record(graph, node_ids) for node_ids in paths]
        node_ids = _deduplicate([node_id for path in paths for node_id in path])
        return AttackPathAnalysis(
            tenant_id=canonical_tenant,
            source_node_id=query.source_node_id,
            target_node_id=query.target_node_id,
            paths=path_records,
            nodes=[graph.nodes[node_id]["record"] for node_id in node_ids],
        )


def _bounded_simple_paths(graph: nx.DiGraph, query: AttackPathQuery) -> list[list[str]]:
    """Enumerate deterministic simple paths without exposing an unbounded graph search."""
    completed: list[list[str]] = []
    pending: deque[list[str]] = deque([[query.source_node_id]])
    explored = 0

    while pending and len(completed) < query.max_paths:
        path = pending.popleft()
        current = path[-1]
        if current == query.target_node_id:
            completed.append(path)
            continue
        if len(path) - 1 >= query.max_hops:
            continue
        for successor in sorted(graph.successors(current)):
            explored += 1
            if explored > MAX_GRAPH_EXPLORATIONS:
                return completed
            if successor not in path:
                pending.append([*path, successor])
    return completed


def _path_record(graph: nx.DiGraph, node_ids: list[str]) -> AttackPath:
    edges = [graph.edges[source, target]["record"] for source, target in zip(node_ids, node_ids[1:])]
    nodes = [graph.nodes[node_id]["record"] for node_id in node_ids]
    evidence_ids = _deduplicate(
        [evidence_id for node in nodes for evidence_id in node.evidence_ids]
        + [evidence_id for edge in edges for evidence_id in edge.evidence_ids]
    )
    return AttackPath(
        node_ids=node_ids,
        edges=edges,
        hop_count=len(edges),
        risk_score=sum(node.risk_score for node in nodes) + sum(edge.risk_score for edge in edges),
        evidence_ids=evidence_ids,
    )


class GovernedAttackPathService:
    """Project canonical evidence and return tenant-isolated, read-only graph analyses."""

    def __init__(self, store: TenantGraphStore | None = None) -> None:
        self._store = store or InMemoryTenantGraphStore()

    async def project_evidence(
        self,
        tenant_id: str,
        *,
        assets: list[HostAssetRecord],
        integrity_observations: list[IntegrityObservation],
        detections: list[DetectionRecord],
        alerts: list[AlertRecord],
        cases: list[CaseRecord],
    ) -> GraphProjectionResult:
        canonical_tenant = _canonical_tenant_id(tenant_id)
        records = [*assets, *integrity_observations, *detections, *alerts, *cases]
        if any(record.tenant_id != canonical_tenant for record in records):
            raise ValueError("Graph projection refuses cross-tenant evidence.")

        nodes: dict[str, AttackGraphNode] = {}
        edges: dict[tuple[str, str], AttackGraphEdge] = {}

        def add_node(node: AttackGraphNode) -> None:
            existing = nodes.get(node.node_id)
            if existing is None:
                nodes[node.node_id] = node
                return
            nodes[node.node_id] = existing.model_copy(
                update={
                    "risk_score": max(existing.risk_score, node.risk_score),
                    "evidence_ids": _deduplicate([*existing.evidence_ids, *node.evidence_ids]),
                    "attributes": {**existing.attributes, **node.attributes},
                }
            )

        def add_edge(edge: AttackGraphEdge) -> None:
            key = (edge.source_node_id, edge.target_node_id)
            existing = edges.get(key)
            if existing is None:
                edges[key] = edge
                return
            if existing.relationship != edge.relationship:
                raise ValueError("A graph snapshot cannot store two relationship types between the same node pair.")
            edges[key] = existing.model_copy(
                update={
                    "risk_score": max(existing.risk_score, edge.risk_score),
                    "evidence_ids": _deduplicate([*existing.evidence_ids, *edge.evidence_ids]),
                }
            )

        asset_node_ids: set[str] = set()
        for asset in assets:
            node_id = f"asset:{asset.asset_id}"
            asset_node_ids.add(node_id)
            add_node(
                AttackGraphNode(
                    node_id=node_id,
                    tenant_id=canonical_tenant,
                    kind="asset",
                    label=asset.hostname,
                    risk_score=15,
                    evidence_ids=[asset.asset_id],
                    attributes={"agent_id": asset.agent_id, "platform": asset.platform, "source": asset.source},
                )
            )

        integrity_node_ids_by_source_event: dict[str, str] = {}
        for observation in integrity_observations:
            asset_node_id = f"asset:{observation.asset_id}"
            if asset_node_id not in asset_node_ids:
                continue
            observation_node_id = f"integrity:{observation.observation_id}"
            integrity_node_ids_by_source_event[observation.source_event_id] = observation_node_id
            risk = _severity_risk(observation.severity)
            add_node(
                AttackGraphNode(
                    node_id=observation_node_id,
                    tenant_id=canonical_tenant,
                    kind="integrity_observation",
                    label=f"{observation.check_type}:{observation.status}",
                    risk_score=risk,
                    evidence_ids=[observation.observation_id, observation.source_event_id],
                    attributes={"check_type": observation.check_type, "status": observation.status, "severity": observation.severity},
                )
            )
            add_edge(
                AttackGraphEdge(
                    source_node_id=observation_node_id,
                    target_node_id=asset_node_id,
                    relationship="INTEGRITY_OBSERVED_ON_ASSET",
                    evidence_ids=[observation.observation_id],
                    risk_score=risk,
                )
            )

        detection_node_ids: set[str] = set()
        for detection in detections:
            detection_node_id = f"detection:{detection.detection_id}"
            detection_node_ids.add(detection_node_id)
            risk = _severity_risk(detection.severity)
            add_node(
                AttackGraphNode(
                    node_id=detection_node_id,
                    tenant_id=canonical_tenant,
                    kind="detection",
                    label=detection.title,
                    risk_score=risk,
                    evidence_ids=[detection.detection_id, detection.event_id],
                    attributes={"rule_id": detection.rule_id, "severity": detection.severity, "status": detection.status},
                )
            )
            asset_id = detection.evidence.get("asset_id")
            asset_node_id = f"asset:{asset_id}" if isinstance(asset_id, str) else None
            if asset_node_id in asset_node_ids:
                add_edge(
                    AttackGraphEdge(
                        source_node_id=detection_node_id,
                        target_node_id=asset_node_id,
                        relationship="DETECTION_OBSERVED_ON_ASSET",
                        evidence_ids=[detection.detection_id],
                        risk_score=risk,
                    )
                )
            observation_node_id = integrity_node_ids_by_source_event.get(detection.event_id)
            if observation_node_id is not None:
                add_edge(
                    AttackGraphEdge(
                        source_node_id=detection_node_id,
                        target_node_id=observation_node_id,
                        relationship="DETECTION_OBSERVED_ON_INTEGRITY",
                        evidence_ids=[detection.detection_id, detection.event_id],
                        risk_score=risk,
                    )
                )
            for mitre in detection.mitre_evidence:
                mitre_node_id = f"mitre:{mitre.technique_id}"
                add_node(
                    AttackGraphNode(
                        node_id=mitre_node_id,
                        tenant_id=canonical_tenant,
                        kind="mitre_technique",
                        label=f"{mitre.technique_id} ({mitre.tactic})",
                        risk_score=0,
                        evidence_ids=[detection.detection_id],
                        attributes={"technique_id": mitre.technique_id, "tactic": mitre.tactic},
                    )
                )
                add_edge(
                    AttackGraphEdge(
                        source_node_id=detection_node_id,
                        target_node_id=mitre_node_id,
                        relationship="DETECTION_MATCHES_MITRE_TECHNIQUE",
                        evidence_ids=[detection.detection_id],
                        risk_score=0,
                    )
                )

        alert_node_ids: set[str] = set()
        for alert in alerts:
            alert_node_id = f"alert:{alert.alert_id}"
            alert_node_ids.add(alert_node_id)
            risk = _severity_risk(alert.severity)
            add_node(
                AttackGraphNode(
                    node_id=alert_node_id,
                    tenant_id=canonical_tenant,
                    kind="alert",
                    label=alert.title,
                    risk_score=risk,
                    evidence_ids=[alert.alert_id, *alert.detection_ids],
                    attributes={"severity": alert.severity, "status": alert.status, "occurrence_count": alert.occurrence_count},
                )
            )
            for detection_id in alert.detection_ids:
                detection_node_id = f"detection:{detection_id}"
                if detection_node_id in detection_node_ids:
                    add_edge(
                        AttackGraphEdge(
                            source_node_id=alert_node_id,
                            target_node_id=detection_node_id,
                            relationship="ALERT_DERIVED_FROM_DETECTION",
                            evidence_ids=[alert.alert_id, detection_id],
                            risk_score=risk,
                        )
                    )

        for case in cases:
            case_node_id = f"case:{case.case_id}"
            risk = _severity_risk(case.severity)
            add_node(
                AttackGraphNode(
                    node_id=case_node_id,
                    tenant_id=canonical_tenant,
                    kind="case",
                    label=case.title,
                    risk_score=risk,
                    evidence_ids=[case.case_id, *case.alert_ids],
                    attributes={"severity": case.severity, "status": case.status},
                )
            )
            for alert_id in case.alert_ids:
                alert_node_id = f"alert:{alert_id}"
                if alert_node_id in alert_node_ids:
                    add_edge(
                        AttackGraphEdge(
                            source_node_id=case_node_id,
                            target_node_id=alert_node_id,
                            relationship="CASE_INVESTIGATES_ALERT",
                            evidence_ids=[case.case_id, alert_id],
                            risk_score=risk,
                        )
                    )

        return await self._store.replace_snapshot(canonical_tenant, list(nodes.values()), list(edges.values()))

    async def analyze(self, tenant_id: str, query: AttackPathQuery) -> AttackPathAnalysis:
        return await self._store.analyze(_canonical_tenant_id(tenant_id), query)
