from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend_api.shared.database import Base
from features.cognitive_core_intelligence.cognitive_core import CognitiveCore
from features.synthetic_cognitive_memory.cognitive_memory import CognitiveMemory


def test_memory_learns_and_recalls_enriched_threat_analysis():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    memory = CognitiveMemory(session)
    core = CognitiveCore(memory)

    new_threat = "zero_day_exploit_variant_XYZ"
    first_analysis = core.analyze_threat(new_threat)

    assert first_analysis["threat_level"] == "critical"

    first_analysis["threat_level"] = "critical"
    first_analysis["description"] = "Enriched Analysis: Confirmed zero-day exploit."
    memory.store_episode(new_threat, first_analysis, "Patched and isolated.")

    second_analysis = core.analyze_threat(new_threat)

    assert second_analysis["threat_level"] == "critical"
    assert "Enriched Analysis" in second_analysis["description"]
    session.close()
