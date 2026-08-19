import os

import pytest
import yaml

from phantomnet_agent.digital_twin.generator import TwinGenerator
from phantomnet_agent.digital_twin.models import TwinTemplate
from phantomnet_agent.digital_twin.sanity_checks import validate_no_real_keys


class RecordingEvidenceVault:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def store_evidence(self, **kwargs):
        self.calls.append(kwargs)
        return "evidence-test-001"


@pytest.fixture
def aws_s3_template() -> TwinTemplate:
    template_path = os.path.join(
        os.path.dirname(__file__), "..", "presets", "aws_s3_template.yaml"
    )
    with open(template_path, encoding="utf-8") as template_file:
        return TwinTemplate(**yaml.safe_load(template_file))


@pytest.mark.asyncio
async def test_render_and_validate(aws_s3_template: TwinTemplate):
    evidence_vault = RecordingEvidenceVault()
    generator = TwinGenerator(evidence_vault=evidence_vault)

    instance = await generator.render_template(aws_s3_template, params={"org": "TestCo"})

    assert "fake_s3" in instance.docker_compose_yaml
    assert instance.template_id == aws_s3_template.template_id
    assert evidence_vault.calls[0]["source"] == "digital_twin_generation"
    assert validate_no_real_keys(aws_s3_template) == []
