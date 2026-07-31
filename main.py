import os
import pickle
from typing import Any, Dict, List

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(ROOT, "Mental_Health_Model.pkl")

app = FastAPI(title="Mental Health Prediction API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StudentPayload(BaseModel):
    Age: int
    Gender: str
    Country: str
    Academic_Level: str
    Most_Used_Platform: str
    Purpose_Of_Use: str
    Avg_Daily_Usage_Hours: float
    Daily_Unlocks: int
    Study_Hours: float
    Physical_Activity_Hours: float
    Sleep_Hours_Per_Night: float
    Stress_Level: str


MODEL = None
TOP_COUNTRIES = ["India", "USA", "UK", "Canada", "Australia", "Germany", "France", "Mexico", "Turkey", "Other"]
EXPECTED_COLUMNS = [
    "Study_Hours",
    "Age",
    "Daily_Unlocks",
    "Physical_Activity_Hours",
    "Sleep_Hours_Per_Night",
    "Stress_Level",
    "Gender",
    "Purpose_Of_Use",
    "group_country",
    "Most_Used_Platform",
]


def load_model() -> Any:
    global MODEL
    if MODEL is None:
        MODEL = joblib.load(MODEL_PATH)
    return MODEL


def _coerce_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "Age": int(payload.get("Age", 0)),
        "Gender": str(payload.get("Gender", "")).strip(),
        "Country": str(payload.get("Country", "")).strip(),
        "Academic_Level": str(payload.get("Academic_Level", "")).strip(),
        "Most_Used_Platform": str(payload.get("Most_Used_Platform", "")).strip(),
        "Purpose_Of_Use": str(payload.get("Purpose_Of_Use", "")).strip(),
        "Avg_Daily_Usage_Hours": float(payload.get("Avg_Daily_Usage_Hours", 0)),
        "Daily_Unlocks": int(payload.get("Daily_Unlocks", 0)),
        "Study_Hours": float(payload.get("Study_Hours", 0)),
        "Physical_Activity_Hours": float(payload.get("Physical_Activity_Hours", 0)),
        "Sleep_Hours_Per_Night": float(payload.get("Sleep_Hours_Per_Night", 0)),
        "Stress_Level": str(payload.get("Stress_Level", "")).strip(),
    }


def _build_feature_frame(payload: Dict[str, Any]) -> pd.DataFrame:
    row = _coerce_payload(payload)
    frame = pd.DataFrame([row])
    if "group_country" not in frame.columns:
        frame["group_country"] = frame["Country"].apply(lambda country: country if country in TOP_COUNTRIES else "Other")
    frame = frame.reindex(columns=EXPECTED_COLUMNS, fill_value="Other")
    return frame


def predict(payload: Dict[str, Any]) -> Dict[str, Any]:
    model = load_model()
    frame = _build_feature_frame(payload)
    prediction = model.predict(frame)[0]

    score = float(np.clip(prediction, 0, 10))
    if score < 4:
        band = "strained"
    elif score < 7:
        band = "balanced"
    else:
        band = "resilient"

    return {"score": round(score, 2), "band": band}


@app.get("/")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/predict")
def predict_endpoint(payload: StudentPayload) -> Dict[str, Any]:
    try:
        return predict(payload.model_dump())
    except Exception as exc:
        return {"error": True, "detail": str(exc)}
