import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

import main


def test_predict_endpoint_uses_model():
    payload = {
        "Age": 21,
        "Gender": "Male",
        "Country": "India",
        "Academic_Level": "Undergraduate",
        "Most_Used_Platform": "Instagram",
        "Purpose_Of_Use": "Education",
        "Avg_Daily_Usage_Hours": 4.0,
        "Daily_Unlocks": 120,
        "Study_Hours": 4.5,
        "Physical_Activity_Hours": 2.2,
        "Sleep_Hours_Per_Night": 6.5,
        "Stress_Level": "Medium",
    }

    result = main.predict(payload)
    assert result["score"] >= 0
    assert result["score"] <= 10
    assert result["band"] in {"strained", "balanced", "resilient"}
