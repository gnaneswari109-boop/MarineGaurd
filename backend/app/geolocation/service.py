def estimate_position(d: dict, metadata: dict | None, image_width: int) -> tuple[float | None, float | None]:
    if not metadata or not metadata.get("latitude") or not metadata.get("longitude"): return None, None
    # Simplified along-track/cross-track prototype calculation; not survey-grade.
    cross_track_m = ((d["x"] + d["w"]/2) / image_width - .5) * float(metadata.get("range", 100))
    return float(metadata["latitude"]), float(metadata["longitude"]) + cross_track_m / 111_320

def severity(d: dict) -> str:
    score = d["final_confidence"] * 60 + min(d["width_m"] * d["height_m"], 30)
    if d["object_class"] == "Ghost Net": score += 22
    if score >= 92: return "CRITICAL"
    if score >= 72: return "HIGH"
    if score >= 50: return "MEDIUM"
    return "LOW"
