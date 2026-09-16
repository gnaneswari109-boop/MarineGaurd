def filter_confidence(d: dict, threshold: float = .5) -> dict | None:
    area = d["w"] * d["h"]
    ratio = d["w"] / max(d["h"], 1)
    penalty = .0 if area > 120 and .08 < ratio < 18 else .18
    confidence = max(0.0, d["raw_confidence"] - penalty)
    if confidence < threshold or d["w"] < 12 or d["h"] < 6: return None
    return d | {"filtered_confidence": confidence, "final_confidence": confidence}
