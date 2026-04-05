# ============================================================
# routes/forecast.py — all /forecast endpoints
# ============================================================

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from app.core import (
    model, le_pmo, le_region, FEATURES,
    FUEL_FEATURES, OIL_FEATURES, MONTH_INV,
    pmo_history, meta, nat_forecast, nat_hist,
    get_fuel, get_oil
)
from app.models.schemas import (
    PMOForecastRequest, PMOForecastResponse,
    NationalResponse
)

router = APIRouter(prefix="/forecast", tags=["Forecast"])

# ── GET /forecast/national ────────────────────────────────────
@router.get("/national")
def get_national():
    """Pre-computed national forecast — fast, no model call needed"""
    return {
        "historical": nat_hist,
        "forecast":   nat_forecast,
        "accuracy":   f"{meta['accuracy_pct']}%",
        "mean_mape":  f"{meta['mean_mape_pct']}%",
    }

# ── GET /forecast/yearly ──────────────────────────────────────
@router.get("/yearly")
def get_yearly():
    """Yearly national totals — historical + forecast"""
    # Aggregate historical monthly → yearly
    hist_yearly = {}
    for row in nat_hist:
        y = row['year']
        hist_yearly[y] = hist_yearly.get(y, 0) + row['total']

    # Aggregate forecast monthly → yearly
    fc_yearly = {}
    for row in nat_forecast:
        y = row['year']
        fc_yearly[y] = fc_yearly.get(y, 0) + row['predicted']

    return {
        "historical": [{"year": y, "total": t} for y, t in sorted(hist_yearly.items())],
        "forecast":   [{"year": y, "total": t} for y, t in sorted(fc_yearly.items())],
    }

# ── GET /forecast/seasonal ────────────────────────────────────
@router.get("/seasonal")
def get_seasonal():
    """Average monthly pattern Jan-Dec (seasonal shape)"""
    hist_by_month = {}
    for row in nat_hist:
        m = row['month_num']
        if m not in hist_by_month:
            hist_by_month[m] = {'total': 0, 'count': 0, 'month': row['month']}
        hist_by_month[m]['total'] += row['total']
        hist_by_month[m]['count'] += 1

    fc_by_month = {}
    for row in nat_forecast:
        m = row['month_num']
        if m not in fc_by_month:
            fc_by_month[m] = {'total': 0, 'count': 0, 'month': row['month']}
        fc_by_month[m]['total'] += row['predicted']
        fc_by_month[m]['count'] += 1

    return {
        "historical": [
            {"month_num": m, "month": v['month'], "avg": v['total'] // v['count']}
            for m, v in sorted(hist_by_month.items())
        ],
        "forecast": [
            {"month_num": m, "month": v['month'], "avg": v['total'] // v['count']}
            for m, v in sorted(fc_by_month.items())
        ],
    }

# ── POST /forecast/pmo ────────────────────────────────────────
@router.post("/pmo")
def forecast_pmo(req: PMOForecastRequest):
    """Generate live forecast for a specific PMO"""
    if req.pmo not in meta['pmo_list']:
        raise HTTPException(400, f"Unknown PMO '{req.pmo}'. Valid: {meta['pmo_list'][:3]}...")

    # Get PMO history from saved JSON
    pmo_data   = pmo_history.get(req.pmo)
    if not pmo_data:
        raise HTTPException(404, f"No history data for PMO: {req.pmo}")

    try:
        pmo_enc    = int(le_pmo.transform([req.pmo])[0])
        region_enc = int(le_region.transform([pmo_data['region']])[0])
    except Exception as e:
        raise HTTPException(500, f"Encoder error: {e}")

    # Rebuild history list
    history    = [row['Total'] for row in pmo_data['history']]
    hist_max   = pmo_data['hist_max']
    hist_min   = pmo_data['hist_min']
    last_year  = pmo_data['last_year']
    last_month = pmo_data['last_month']
    min_yr     = 2016
    mean_mape  = meta['mean_mape']
    results    = []

    for step in range(req.n_months):
        next_month = last_month % 12 + 1
        next_year  = last_year + (1 if last_month == 12 else 0)
        last_month, last_year = next_month, next_year
        nm_str = MONTH_INV[next_month]

        def get_lag(lag):
            idx = len(history) - lag
            return float(history[idx]) if idx >= 0 else float(history[0])

        lag1  = get_lag(1);  lag2 = get_lag(2);  lag3  = get_lag(3)
        lag6  = get_lag(6);  lag12 = get_lag(12)
        r3m   = float(np.mean(history[-3:]))  if len(history) >= 3  else float(np.mean(history))
        r3s   = float(np.std(history[-3:]))   if len(history) >= 3  else 0.0
        r12m  = float(np.mean(history[-12:])) if len(history) >= 12 else float(np.mean(history))
        sml   = float(history[-12]) if len(history) >= 12 else r12m
        yoy   = 0.05  # modest growth assumption for future months

        q  = (next_month - 1) // 3 + 1
        fv = get_fuel(next_year, nm_str)
        ov = get_oil(next_year, nm_str)

        row = pd.DataFrame([{
            'YearIndex':      next_year - min_yr,
            'TimeIndex':      (next_year - min_yr) * 12 + (next_month - 1),
            'Month_sin':      float(np.sin(2 * np.pi * next_month / 12)),
            'Month_cos':      float(np.cos(2 * np.pi * next_month / 12)),
            'Quarter_sin':    float(np.sin(2 * np.pi * q / 4)),
            'Quarter_cos':    float(np.cos(2 * np.pi * q / 4)),
            'PMO_encoded':    pmo_enc,
            'Region_encoded': region_enc,
            'IsHolidayMonth': 1 if nm_str in ['Dec','Jan','Apr','Oct','Nov'] else 0,
            'IsSummerMonth':  1 if nm_str in ['Mar','Apr','May'] else 0,
            'Lag_1': lag1, 'Lag_2': lag2, 'Lag_3': lag3,
            'Lag_6': lag6, 'Lag_12': lag12,
            'Rolling3_mean': r3m, 'Rolling3_std': r3s, 'Rolling12_mean': r12m,
            'YoY_growth': yoy, 'SameMonthLastYear': sml,
            **{k: float(fv.get(k, 0)) for k in FUEL_FEATURES},
            **{k: float(ov.get(k, 0)) for k in OIL_FEATURES},
        }])

        pred = float(model.predict(row[FEATURES])[0])
        pred = max(pred, 0)
        hw   = min(step / 12.0, 0.6)
        pred = (1 - hw) * pred + hw * r12m
        pred = float(np.clip(pred, hist_min * 0.6, hist_max * 1.4))

        results.append({
            "year":      next_year,
            "month":     nm_str,
            "month_num": next_month,
            "date":      f"{next_year}-{str(next_month).zfill(2)}-01",
            "predicted": int(round(pred)),
            "lower":     int(round(pred * (1 - mean_mape))),
            "upper":     int(round(pred * (1 + mean_mape))),
            "oil_shock": bool(ov.get("Oil_Shock_Flag", 0)),
        })
        history.append(pred)

    return {
        "pmo":      req.pmo,
        "region":   pmo_data['region'],
        "forecast": results,
        "meta": {
            "mean_mape":  round(mean_mape * 100, 1),
            "confidence": f"±{round(mean_mape * 100)}%",
            "n_months":   req.n_months,
        },
    }

# ── GET /forecast/folds ───────────────────────────────────────
@router.get("/folds")
def get_folds():
    """CV fold accuracy results for dashboard chart"""
    periods = ["2017-2019","2019-2021","2021-2022","2022-2024","2024-2025"]
    folds   = meta.get("fold_results", [])
    return {
        "folds": [
            {**f, "period": periods[i] if i < len(periods) else ""}
            for i, f in enumerate(folds)
        ],
        "mean_mape":     meta["mean_mape_pct"],
        "mean_accuracy": meta["accuracy_pct"],
    }
