from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime
from uuid import uuid4
import csv, io, logging
import numpy as np
from PIL import Image
from .database.db import Base, engine, get_db
from .models.entities import Survey, Detection
from .ai.model_adapter import get_model
from .preprocessing.sonar import preprocess
from .services.anomaly_filter import filter_anomalies
from .geolocation.service import estimate_position, severity
from .reporting.exports import csv_report, json_report, records

logging.basicConfig(level=logging.INFO)
app=FastAPI(title="MARINEGUARD AI", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])
UPLOADS=Path(__file__).resolve().parents[2]/"uploads"; UPLOADS.mkdir(exist_ok=True)
Base.metadata.create_all(bind=engine)
ALLOWED={"image/png","image/jpeg","image/tiff"}

def serialise(d):
    return {"id":d.id,"survey_id":d.survey_id,"object_class":d.object_class,"confidence":d.confidence,"raw_confidence":d.raw_confidence,"latitude":d.latitude,"longitude":d.longitude,"width_m":d.width_m,"height_m":d.height_m,"severity":d.severity,"status":d.status,"bbox":{"x":d.x,"y":d.y,"w":d.w,"h":d.h},"timestamp":d.created_at.isoformat()}

@app.get("/api/system/status")
def system_status(db: Session=Depends(get_db)):
    model, mode=get_model(); return {"status":"ONLINE","inference":"READY","model":mode,"survey_count":db.query(Survey).count(),"detection_count":db.query(Detection).count()}

@app.get("/api/model/status")
def model_status():
    _, mode=get_model(); return {"model":mode,"status":"READY","version":"v1.0","classes":8,"threshold":.5,"note":"Prototype / Demonstration Model" if mode=="Demo Model" else "YOLO weights loaded"}

@app.post("/api/surveys/upload")
async def upload_survey(image: UploadFile=File(...), metadata: UploadFile|None=File(None), db: Session=Depends(get_db)):
    if image.content_type not in ALLOWED: raise HTTPException(415,"Unsupported image. Use PNG, JPG, JPEG, or TIFF.")
    payload=await image.read()
    if len(payload)>20*1024*1024: raise HTTPException(413,"Image exceeds 20 MB limit.")
    try: Image.open(io.BytesIO(payload)).verify()
    except Exception: raise HTTPException(400,"The uploaded file is not a valid sonar image.")
    sid=f"SURVEY-{datetime.now():%Y}-{str(uuid4())[:5].upper()}"; ext=Path(image.filename or "sonar.png").suffix.lower(); path=UPLOADS/f"{sid}{ext}"; path.write_bytes(payload)
    meta_path=None
    if metadata:
        if Path(metadata.filename or "").suffix.lower() not in {".csv",".json"}: raise HTTPException(415,"Metadata must be CSV or JSON.")
        meta_path=UPLOADS/f"{sid}_metadata{Path(metadata.filename).suffix.lower()}"; meta_path.write_bytes(await metadata.read())
    survey=Survey(id=sid,name=image.filename or sid,image_path=str(path),metadata_path=str(meta_path) if meta_path else None); db.add(survey); db.commit()
    im=Image.open(path); return {"survey_id":sid,"file_name":survey.name,"resolution":list(im.size),"metadata_status":"available" if meta_path else "missing"}

def metadata_for(survey):
    if not survey.metadata_path: return None
    p=Path(survey.metadata_path)
    try:
        if p.suffix==".json": import json; data=json.loads(p.read_text()); return data[0] if isinstance(data,list) else data
        return next(csv.DictReader(p.read_text().splitlines()))
    except Exception: return None

@app.post("/api/analyze")
def analyze(survey_id: str=Form(...), preprocessing_enabled: bool=Form(True), threshold: float=Form(.5), db: Session=Depends(get_db)):
    survey=db.get(Survey,survey_id)
    if not survey: raise HTTPException(404,"Survey not found")
    image=np.array(Image.open(survey.image_path).convert("RGB")); processed=preprocess(image, preprocessing_enabled)
    model,mode=get_model(); raw=model.detect(processed); final=filter_anomalies(raw, threshold); meta=metadata_for(survey); db.query(Detection).filter(Detection.survey_id==survey_id).delete()
    for d in final:
        d["width_m"]=round(d["w"] / image.shape[1] * float((meta or {}).get("range",100)),2); d["height_m"]=round(d["h"] / image.shape[0] * 30,2)
        lat,lon=estimate_position(d,meta,image.shape[1]); d["severity"]=severity(d)
        db.add(Detection(id=str(uuid4())[:8].upper(),survey_id=survey_id,object_class=d["object_class"],confidence=d["final_confidence"],raw_confidence=d["raw_confidence"],latitude=lat,longitude=lon,width_m=d["width_m"],height_m=d["height_m"],severity=d["severity"],x=d["x"],y=d["y"],w=d["w"],h=d["h"]))
    db.commit(); detections=db.query(Detection).filter_by(survey_id=survey_id).all()
    return {"survey_id":survey_id,"model":mode,"preprocessing_applied":preprocessing_enabled,"raw_count":len(raw),"filtered_count":len(detections),"false_positive_reduction":round((1-len(detections)/max(len(raw),1))*100,1),"metadata_available":bool(meta),"detections":[serialise(d) for d in detections]}

@app.get("/api/surveys")
def surveys(db:Session=Depends(get_db)):
    return [{"id":s.id,"name":s.name,"created_at":s.created_at.isoformat(),"status":s.status,"detections":db.query(Detection).filter_by(survey_id=s.id).count()} for s in db.query(Survey).order_by(Survey.created_at.desc()).all()]
@app.get("/api/surveys/{survey_id}")
def survey(survey_id:str,db:Session=Depends(get_db)):
    s=db.get(Survey,survey_id)
    if not s: raise HTTPException(404,"Survey not found")
    return {"id":s.id,"name":s.name,"image_url":f"/uploads/{Path(s.image_path).name}","detections":[serialise(d) for d in db.query(Detection).filter_by(survey_id=s.id)]}
@app.get("/api/detections")
def detections(survey_id:str|None=None,db:Session=Depends(get_db)):
    q=db.query(Detection); q=q.filter_by(survey_id=survey_id) if survey_id else q; return [serialise(d) for d in q.all()]
@app.get("/api/detections/{detection_id}")
def detection(detection_id:str,db:Session=Depends(get_db)):
    d=db.get(Detection,detection_id)
    if not d: raise HTTPException(404,"Detection not found")
    return serialise(d)
@app.get("/api/reports/{survey_id}/csv")
def report_csv(survey_id:str,db:Session=Depends(get_db)):
    return Response(csv_report(db.query(Detection).filter_by(survey_id=survey_id).all()),media_type="text/csv",headers={"Content-Disposition":f"attachment; filename={survey_id}.csv"})
@app.get("/api/reports/{survey_id}/json")
def report_json(survey_id:str,db:Session=Depends(get_db)):
    return Response(json_report(survey_id,db.query(Detection).filter_by(survey_id=survey_id).all()),media_type="application/json",headers={"Content-Disposition":f"attachment; filename={survey_id}.json"})
@app.post("/api/demo/load")
def demo(db:Session=Depends(get_db)):
    # Frontend uses generated demo image data; this endpoint communicates demo readiness.
    return {"ready":True,"message":"Demo survey ready for analysis"}
app.mount("/uploads", StaticFiles(directory=UPLOADS), name="uploads")
