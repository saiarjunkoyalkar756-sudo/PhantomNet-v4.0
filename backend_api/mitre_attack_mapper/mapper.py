import json
import logging
import os
import httpx
from stix2 import MemoryStore, Filter, AttackPattern, Technique

logger = logging.getLogger(__name__)

# URL for the MITRE ATT&CK Enterprise CTI in STIX format
MITRE_CTI_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"


def fetch_mitre_cti_data():
    """
    Fetches the latest MITRE ATT&CK CTI data in STIX format.
    """
    logger.info(f"Fetching MITRE ATT&CK CTI data from {MITRE_CTI_URL}...")
    try:
        response = httpx.get(MITRE_CTI_URL)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to fetch MITRE CTI data: {e}")
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while fetching MITRE CTI data: {e}",
            exc_info=True,
        )
    return None


def load_mitre_data(output_file: str):
    """
    Loads MITRE ATT&CK data from a local file or fetches it if not present.
    """
    if os.path.exists(output_file):
        logger.info(f"Loading MITRE data from local file: {output_file}")
        with open(output_file, "r") as f:
            mitre_data = json.load(f)
            # For simplicity, we just return the techniques directly.
            # In a real app, you'd load into a MemoryStore or similar.
            return mitre_data.get("techniques", [])
    else:
        logger.info("Local MITRE data not found, fetching from MITRE CTI...")
        stix_data = fetch_mitre_cti_data()
        if stix_data:
            store = MemoryStore(stix_data=stix_data)
            techniques = store.query(Filter("type", "=", "attack-pattern"))

            processed_techniques = []
            for tech in techniques:
                processed_techniques.append(
                    {
                        "id": tech.id,
                        "name": tech.name,
                        "description": tech.description,
                        "external_references": [
                            {
                                "source_name": ref.source_name,
                                "url": ref.url,
                                "external_id": ref.external_id,
                            }
                            for ref in tech.external_references
                            if hasattr(ref, "url")
                        ],
                        "kill_chain_phases": (
                            [phase.phase_name for phase in tech.kill_chain_phases]
                            if hasattr(tech, "kill_chain_phases")
                            else []
                        ),
                    }
                )

            with open(output_file, "w") as f:
                json.dump(
                    {"techniques": processed_techniques, "last_updated": time.time()},
                    f,
                    indent=4,
                )
            logger.info(
                f"MITRE data fetched and saved to {output_file}. Total techniques: {len(processed_techniques)}"
            )
            return processed_techniques
        logger.warning("Could not load MITRE data.")
        return []


def map_event_to_techniques(event: dict, mitre_data_file: str):
    """
    Maps a security event to relevant MITRE ATT&CK techniques.
    """
    techniques = load_mitre_data(mitre_data_file)
    mapped_techniques = []

    event_description = event.get("details", {}).get("message", "").lower()
    event_type = event.get("event_type", "").lower()

    # Simple keyword-based mapping (placeholder for real ML/regex based mapping)
    for tech in techniques:
        tech_name_lower = tech["name"].lower()
        tech_description_lower = tech["description"].lower()

        if (
            tech_name_lower in event_description
            or tech_description_lower in event_description
        ):
            mapped_techniques.append(
                {"id": tech["id"], "name": tech["name"], "confidence": 0.7}
            )
        elif "phishing" in event_description and "phishing" in tech_name_lower:
            mapped_techniques.append(
                {"id": tech["id"], "name": tech["name"], "confidence": 0.9}
            )
        elif "malware" in event_description and "execution" in tech_name_lower:
            mapped_techniques.append(
                {"id": tech["id"], "name": tech["name"], "confidence": 0.8}
            )

    return mapped_techniques


if __name__ == "__main__":
    # For testing purposes
    load_mitre_data("mitre_data.json")

    sample_event = {
        "event_id": "evt-123",
        "event_type": "alert",
        "details": {
            "message": "Suspicious process execution detected, possibly malware."
        },
    }
    mapped = map_event_to_techniques(sample_event, "mitre_data.json")
    print(f"Mapped techniques for sample event: {mapped}")
