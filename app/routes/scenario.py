# ============================================================
# routes/scenario.py — oil shock scenario endpoints
# ============================================================

from fastapi import APIRouter, HTTPException
from app.core import meta
from app.models.schemas import ScenarioRequest, ScenarioResult

router = APIRouter(prefix="/scenario", tags=["Scenario"])

SCENARIOS = {
    "baseline":  0.00,
    "mild":      0.15,
    "moderate":  0.35,
    "severe":    0.60,
}
ELASTICITY      = -0.025
CURRENT_DIESEL  = 1.0458   # USD/liter — Mar 2025 last known
PHP_PER_USD     = 57.0

@router.get("/options")
def get_options():
    """Return available scenario options for frontend dropdown"""
    return {
        "scenarios": [
            {"key": "baseline",  "label": "No Shock",         "oil_pct": 0,   "color": "#16a34a"},
            {"key": "mild",      "label": "Mild (+15%)",       "oil_pct": 15,  "color": "#d97706"},
            {"key": "moderate",  "label": "Moderate (+35%)",   "oil_pct": 35,  "color": "#f97316"},
            {"key": "severe",    "label": "Strait Closure (+60%)", "oil_pct": 60, "color": "#dc2626"},
        ],
        "elasticity":    ELASTICITY,
        "note": "MARINA approved 20% fare hike on March 16 2026 — validates this model",
    }

@router.post("/apply")
def apply_scenario(req: ScenarioRequest):
    """Apply oil shock scenario to 2026 baseline forecast"""
    if req.scenario not in SCENARIOS:
        raise HTTPException(400, f"Unknown scenario. Use: {list(SCENARIOS.keys())}")

    pct           = SCENARIOS[req.scenario]
    demand_change = ELASTICITY * (pct / 0.10)
    baseline      = meta["national_forecast"]["2026"]
    adjusted      = baseline * (1 + demand_change)

    return ScenarioResult(
        scenario          = req.scenario,
        oil_change_pct    = pct * 100,
        demand_change_pct = round(demand_change * 100, 1),
        baseline_M        = round(baseline / 1e6, 2),
        adjusted_M        = round(adjusted / 1e6, 2),
        diesel_usd        = round(CURRENT_DIESEL * (1 + pct), 4),
        diesel_php        = round(CURRENT_DIESEL * (1 + pct) * PHP_PER_USD, 0),
    )

@router.get("/all")
def all_scenarios():
    """Return all 4 scenario results at once — for bar chart"""
    baseline = meta["national_forecast"]["2026"]
    results  = []
    for key, pct in SCENARIOS.items():
        demand_change = ELASTICITY * (pct / 0.10)
        adjusted      = baseline * (1 + demand_change)
        results.append({
            "scenario":          key,
            "oil_change_pct":    pct * 100,
            "demand_change_pct": round(demand_change * 100, 1),
            "adjusted_M":        round(adjusted / 1e6, 2),
            "diesel_usd":        round(CURRENT_DIESEL * (1 + pct), 4),
            "diesel_php":        round(CURRENT_DIESEL * (1 + pct) * PHP_PER_USD, 0),
        })
    return {"scenarios": results, "baseline_M": round(baseline / 1e6, 2)}
