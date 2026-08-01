import os
import pickle
from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np
import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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


def _fallback_score(payload: Dict[str, Any]) -> float:
    coerced = _coerce_payload(payload)
    stress = str(coerced.get("Stress_Level", "")).strip().lower()
    sleep = float(coerced.get("Sleep_Hours_Per_Night", 0) or 0)
    usage = float(coerced.get("Avg_Daily_Usage_Hours", 0) or 0)
    unlocks = int(coerced.get("Daily_Unlocks", 0) or 0)
    activity = float(coerced.get("Physical_Activity_Hours", 0) or 0)
    study = float(coerced.get("Study_Hours", 0) or 0)

    score = 7.5
    if stress in {"high", "very high"}:
        score -= 1.6
    elif stress == "medium":
        score -= 0.5

    if sleep < 6:
        score -= 0.9
    elif sleep < 7:
        score -= 0.4

    if usage > 6:
        score -= 1.2
    elif usage > 4:
        score -= 0.6

    if unlocks > 120:
        score -= 0.8
    elif unlocks > 80:
        score -= 0.3

    if activity < 1.5:
        score -= 0.7
    elif activity < 2.5:
        score -= 0.3

    if study < 3:
        score -= 0.7
    elif study < 4:
        score -= 0.3

    return float(np.clip(score, 0, 10))


def _score_to_result(score: float) -> Dict[str, Any]:
    score = float(np.clip(score, 0, 10))
    if score < 4:
        band = "strained"
    elif score < 7:
        band = "balanced"
    else:
        band = "resilient"

    return {"score": round(score, 2), "band": band}


def predict(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        model = load_model()
        frame = _build_feature_frame(payload)
        prediction = model.predict(frame)[0]
        score = float(np.clip(prediction, 0, 10))
    except Exception:
        score = _fallback_score(payload)

    return _score_to_result(score)


ROOT_DIR = Path(__file__).resolve().parent
INDEX_PATH = ROOT_DIR / "index.html"
STATIC_FILES = ["style.css", "script.js"]


@app.get("/")
def index() -> Response:
    return FileResponse(INDEX_PATH)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/{filename}")
def serve_static(filename: str) -> Response:
    if filename in STATIC_FILES:
        return FileResponse(ROOT_DIR / filename)
    raise HTTPException(status_code=404, detail="Not found")


@app.post("/predict")
def predict_endpoint(payload: StudentPayload) -> Dict[str, Any]:
    try:
        return predict(payload.model_dump())
    except Exception as exc:
        return {"error": True, "detail": str(exc)}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=2200, log_level="info")
