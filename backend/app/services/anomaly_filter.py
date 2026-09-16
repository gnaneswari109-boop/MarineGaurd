from .confidence_filter import filter_confidence
def filter_anomalies(detections: list[dict], threshold: float=.5) -> list[dict]:
    return [out for d in detections if (out := filter_confidence(d, threshold)) is not None and out["object_class"] != "Natural Formation"]
