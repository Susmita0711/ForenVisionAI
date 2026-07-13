import os
from typing import Any, Dict

try:
    import cv2
except ImportError:  # pragma: no cover - optional dependency fallback
    cv2 = None


def compare_fingerprints(image_a_path: str, image_b_path: str) -> Dict[str, Any]:
    if not os.path.exists(image_a_path) or not os.path.exists(image_b_path):
        raise FileNotFoundError("Both fingerprint images must exist")

    if cv2 is None:
        return {
            "similarity": 0.0,
            "decision": "review",
            "summary": "OpenCV is unavailable in this environment; fingerprint comparison used a fallback pathway.",
            "match_count": 0,
        }

    image_a = cv2.imread(image_a_path, cv2.IMREAD_GRAYSCALE)
    image_b = cv2.imread(image_b_path, cv2.IMREAD_GRAYSCALE)

    if image_a is None or image_b is None:
        raise ValueError("Unable to read one or both fingerprint images")

    orb = cv2.ORB_create()
    keypoints_a, descriptors_a = orb.detectAndCompute(image_a, None)
    keypoints_b, descriptors_b = orb.detectAndCompute(image_b, None)

    if descriptors_a is None or descriptors_b is None:
        return {
            "similarity": 0.0,
            "decision": "insufficient-features",
            "summary": "The supplied images did not yield enough matching features.",
        }

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    matches = matcher.knnMatch(descriptors_a, descriptors_b, k=2)

    good_matches = []
    for first_match, second_match in matches:
        if first_match.distance < 0.75 * second_match.distance:
            good_matches.append(first_match)

    total_candidates = max(len(keypoints_a), len(keypoints_b), 1)
    similarity = round((len(good_matches) / total_candidates) * 100, 2)
    similarity = max(0.0, min(99.9, similarity))

    if similarity >= 70.0:
        decision = "match"
        summary = "The fingerprints show a strong similarity index and warrant human review."
    elif similarity >= 40.0:
        decision = "review"
        summary = "The fingerprints share moderate overlap and should be reviewed manually."
    else:
        decision = "no-match"
        summary = "The fingerprints do not appear to match under the current comparison profile."

    return {
        "similarity": similarity,
        "decision": decision,
        "summary": summary,
        "match_count": len(good_matches),
    }
