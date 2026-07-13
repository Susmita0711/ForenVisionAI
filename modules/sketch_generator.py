from typing import Any, Dict


def generate_sketch(profile: Dict[str, Any]) -> Dict[str, Any]:
    hair = profile.get("hair", "unknown")
    eyes = profile.get("eyes", "unknown")
    build = profile.get("build", "unknown")
    clothing = profile.get("clothing", "unknown")
    features = profile.get("features", "unknown")

    composite_profile = {
        "hair": hair,
        "eyes": eyes,
        "build": build,
        "clothing": clothing,
        "notable_features": features,
        "confidence": "medium",
    }

    return {
        "composite_profile": composite_profile,
        "workflow_status": "mock synthesis complete",
        "summary": (
            f"A mock composite sketch profile was assembled from witness input with a {composite_profile['confidence']} confidence tier."
        ),
    }
