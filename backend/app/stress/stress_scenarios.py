# app/stress/stress_scenarios.py
from app.stress.stress_models import StressVector


PRESET_STRESS_SCENARIOS = {
    "increased_concurrency": StressVector(
        name="increased_concurrency",
        description="More simultaneous users than initially assumed",
        target_layers=["ui", "hooks", "services"],
        severity=0.8,
    ),

    "team_scale": StressVector(
        name="team_scale",
        description="Multiple teams modifying the codebase",
        target_layers=["utils", "services", "models"],
        severity=0.6,
    ),

    "api_instability": StressVector(
        name="api_instability",
        description="External backend APIs change or become unreliable",
        target_layers=["api", "ui"],
        severity=0.7,
    ),
}
