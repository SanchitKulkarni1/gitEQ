# app/stress/stress_models.py
from pydantic import BaseModel
from typing import List, Dict


class StressVector(BaseModel):
    name: str
    description: str
    target_layers: List[str]
    severity: float


class StressResult(BaseModel):
    stress: str
    violated_assumptions: List[Dict]
    affected_files: List[str]
    impact_path: List[str]
    failure_mode: str
    confidence: float
