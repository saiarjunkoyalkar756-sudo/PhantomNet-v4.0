import pytest

from backend_api.microsegmentation_service import main as microsegmentation


@pytest.mark.asyncio
async def test_get_network_segments_uses_standard_success_envelope():
    response = await microsegmentation.get_network_segments()

    assert response["success"] is True
    assert response["error"] is None
    assert response["data"] == [
        {"id": "1", "name": "HR", "subnets": ["10.0.1.0/24"]},
        {"id": "2", "name": "Finance", "subnets": ["10.0.2.0/24"]},
        {"id": "3", "name": "Engineering", "subnets": ["10.0.3.0/24"]},
    ]


@pytest.mark.asyncio
async def test_create_network_segment_returns_validated_segment_in_envelope():
    segment = microsegmentation.NetworkSegment(
        id="4", name="Marketing", subnets=["10.0.4.0/24"]
    )

    response = await microsegmentation.create_network_segment(segment)

    assert response["success"] is True
    assert response["data"] == segment


@pytest.mark.asyncio
async def test_network_topology_reflects_in_memory_graph_without_broker_access():
    microsegmentation.network_graph.clear()
    microsegmentation.network_graph.add_edge("10.0.1.10", "10.0.2.15")

    response = await microsegmentation.get_network_topology()

    assert response["success"] is True
    assert {node["id"] for node in response["data"]["nodes"]} == {"10.0.1.10", "10.0.2.15"}
    assert response["data"]["links"] == [{"source": "10.0.1.10", "target": "10.0.2.15"}]


@pytest.mark.asyncio
async def test_network_threats_and_violations_are_enveloped():
    violations = await microsegmentation.get_segmentation_violations()
    threats = await microsegmentation.get_network_threats()

    assert violations["success"] is True
    assert violations["data"][0]["source_ip"] == "10.0.1.10"
    assert threats["success"] is True
    assert threats["data"][0]["type"] == "Port Scan"
