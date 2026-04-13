import pytest
import os
from phantomnet_agent.digital_twin.generator import render_template
from phantomnet_agent.digital_twin.sanity_checks import validate_no_real_keys
from phantomnet_agent.digital_twin.models import TwinTemplate
import yaml


@pytest.fixture
def aws_s3_template():
    template_path = os.path.join(
        os.path.dirname(__file__), "..", "presets", "aws_s3_template.yaml"
    )
    with open(template_path, "r") as f:
        data = yaml.safe_load(f)
    return TwinTemplate(**data)


def test_render_and_validate(aws_s3_template):
    inst = render_template(aws_s3_template, params={"org": "TestCo"})
    assert "fake_s3" in inst.docker_compose_yaml
    problems = validate_no_real_keys(aws_s3_template)
    assert problems == []
