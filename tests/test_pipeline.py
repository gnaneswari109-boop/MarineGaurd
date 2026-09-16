import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import numpy as np
from app.preprocessing.sonar import preprocess
from app.ai.model_adapter import DemoModel
from app.services.anomaly_filter import filter_anomalies
from app.geolocation.service import estimate_position, severity

def test_preprocessing_retains_shape():
    assert preprocess(np.zeros((40, 60, 3), dtype=np.uint8)).shape == (40, 60)
def test_demo_is_deterministic():
    image=np.zeros((100,200),dtype=np.uint8); assert DemoModel().detect(image)==DemoModel().detect(image)
def test_filter_and_position():
    d=filter_anomalies(DemoModel().detect(np.zeros((200,300),dtype=np.uint8)))[0]; d |= {"width_m":8,"height_m":3}; assert severity(d) in {"HIGH","CRITICAL"}; assert estimate_position(d,{"latitude":15.1,"longitude":78.1,"range":100},300)[0]==15.1
