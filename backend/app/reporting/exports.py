import csv, io, json
def records(detections):
    return [{"id": d.id, "survey_id": d.survey_id, "object_class": d.object_class, "confidence": d.confidence, "latitude": d.latitude, "longitude": d.longitude, "width_m": d.width_m, "height_m": d.height_m, "severity": d.severity, "status": d.status, "timestamp": d.created_at.isoformat()} for d in detections]
def csv_report(detections):
    rows=records(detections); output=io.StringIO(); writer=csv.DictWriter(output, fieldnames=list(rows[0]) if rows else ["id"]); writer.writeheader(); writer.writerows(rows); return output.getvalue()
def json_report(survey_id, detections): return json.dumps({"survey_id":survey_id,"detections":records(detections)}, indent=2)
