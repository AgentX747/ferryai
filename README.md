# Ferry Passenger Prediction — FastAPI Backend

## Quick Start

### 1. Create virtual environment
```bash
cd ferry-api
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Copy model files
Copy all 10 files from your Anaconda project folder into `model_files/`:
- ferry_model.pkl
- le_pmo.pkl
- le_region.pkl
- features_list.pkl
- fuel_lookup.json
- oil_lookup.json
- pmo_history.json
- model_meta.json
- national_forecast.json
- national_historical.json

### 4. Run the server
```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Test it
Open browser → http://localhost:8000/docs

## Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET  | /              | Health check |
| GET  | /model-info    | Model metadata |
| GET  | /pmos          | All PMO names |
| GET  | /forecast/national  | Pre-computed national forecast |
| GET  | /forecast/yearly    | Yearly totals |
| GET  | /forecast/seasonal  | Monthly seasonal pattern |
| POST | /forecast/pmo       | Live PMO forecast |
| GET  | /forecast/folds     | CV accuracy results |
| GET  | /scenario/options   | Available scenarios |
| POST | /scenario/apply     | Apply one scenario |
| GET  | /scenario/all       | All 4 scenarios at once |
