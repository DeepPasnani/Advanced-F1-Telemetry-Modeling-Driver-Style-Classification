# Model Improvements — Phase 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add weather-aware features and multi-lap aggregation to the F1 telemetry analysis pipeline.

**Architecture:** Two new capabilities bolt into existing `data_loader.py` and `feature_engineering.py` without changing the API contract. `get_weather()` reads from FastF1's built-in weather data. `get_driver_telemetry()` gains a `laps` parameter to return all laps instead of just the fastest. `extract_features()` detects multi-lap data and produces per-lap mean/std features plus weather columns.

**Tech Stack:** Python 3.12+, FastF1, pandas, scikit-learn

## Global Constraints

- Core modules stay at root level (runnable standalone)
- FastF1 cache at `cache/` (already populated with 2023 Bahrain data)
- Tests run via: `python -m pytest tests/test_*.py -v`
- Existing API contract unchanged (no new endpoints)
- All 19 existing tests must still pass after changes

---

### Task 1: Add `get_weather()` to data_loader

**Files:**
- Modify: `data_loader.py`
- Test: `tests/test_data_loader.py`

**Interfaces:**
- Consumes: FastF1 `session` object with `weather_data` attribute
- Produces: `get_weather(session) -> dict`

- [ ] **Step 1: Add test for `get_weather()`**

Add to `tests/test_data_loader.py`:

```python
def test_get_weather(self):
    session = dl.load_session(2023, "Bahrain", "R")
    weather = dl.get_weather(session)
    assert isinstance(weather, dict)
    assert "track_temp" in weather
    assert "air_temp" in weather
    assert "rainfall" in weather
    assert isinstance(weather["track_temp"], (int, float))
    assert isinstance(weather["air_temp"], (int, float))
    assert isinstance(weather["rainfall"], bool)
```

- [ ] **Step 2: Run existing tests to confirm they pass, new test fails**

```bash
python -m pytest tests/test_data_loader.py -v 2>&1 | tail -10
```
Expected: new test fails with `AttributeError: module 'data_loader' has no attribute 'get_weather'`

- [ ] **Step 3: Implement `get_weather()`**

Add to `data_loader.py` after `get_result()`:

```python
def get_weather(session) -> dict:
    """Return average weather conditions for a session.

    Returns dict with track_temp, air_temp (float °C) and rainfall (bool).
    """
    weather = session.weather_data
    if weather is None or weather.empty:
        return {"track_temp": 0.0, "air_temp": 0.0, "rainfall": False}
    return {
        "track_temp": float(weather["TrackTemp"].mean()),
        "air_temp": float(weather["AirTemp"].mean()),
        "rainfall": bool(weather["Rainfall"].any()),
    }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_data_loader.py::TestDataLoader::test_get_weather -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add data_loader.py tests/test_data_loader.py
git commit -m "feat: add get_weather() to data_loader"
```

---

### Task 2: Add multi-lap support to `get_driver_telemetry()`

**Files:**
- Modify: `data_loader.py`
- Test: `tests/test_data_loader.py`

**Interfaces:**
- Consumes: `session`, `driver_code`, `laps="fastest"` param
- Produces: `get_driver_telemetry(session, driver_code, laps="fastest") -> pd.DataFrame`
  - `laps="fastest"` returns single lap (current behavior, backwards compatible)
  - `laps="all"` returns concatenated telemetry for all laps, with `LapNumber` column

- [ ] **Step 1: Add test for multi-lap telemetry**

Add to `tests/test_data_loader.py`:

```python
def test_get_driver_telemetry_all_laps(self):
    session = dl.load_session(2023, "Bahrain", "R")
    telemetry = dl.get_driver_telemetry(session, "VER", laps="all")
    assert isinstance(telemetry, pd.DataFrame)
    assert not telemetry.empty
    assert "LapNumber" in telemetry.columns
    assert "Speed" in telemetry.columns
    # Should have more rows than a single fastest lap
    fast = dl.get_driver_telemetry(session, "VER")
    assert len(telemetry) > len(fast)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_data_loader.py::TestDataLoader::test_get_driver_telemetry_all_laps -v
```
Expected: FAIL (TypeError about `laps` unexpected keyword arg)

- [ ] **Step 3: Update `get_driver_telemetry()`**

Replace the existing function:

```python
def get_driver_telemetry(session: Session, driver_code: str, laps: str = "fastest") -> pd.DataFrame:
    """Return telemetry DataFrame for a driver.

    Args:
        session: Loaded FastF1 session.
        driver_code: Three-letter driver abbreviation.
        laps: "fastest" (single fastest lap) or "all" (all completed laps).

    Returns:
        DataFrame with Distance, Speed, Throttle, Brake, RPM, Gear, nGear.
        If laps="all", also includes LapNumber column.
    """
    laps_data = session.laps.pick_drivers(driver_code)
    if laps_data.empty:
        raise DriverNotFound(f"Driver '{driver_code}' not found in session")
    
    cols = ["Distance", "Speed", "Throttle", "Brake", "RPM", "Gear", "nGear"]
    existing_cols = [c for c in cols if c in laps_data.iloc[0].get_car_data().columns 
                     if hasattr(laps_data.iloc[0], 'get_car_data')]
    
    if laps == "all":
        telemetry_list = []
        for _, lap in laps_data.iterrows():
            lap_telemetry = lap.get_car_data()
            lap_telemetry = lap_telemetry[[c for c in cols if c in lap_telemetry.columns]]
            lap_telemetry["LapNumber"] = lap["LapNumber"]
            telemetry_list.append(lap_telemetry)
        return pd.concat(telemetry_list, ignore_index=True)
    else:
        fastest = laps_data.pick_fastest()
        telemetry = fastest.get_car_data()
        return telemetry[[c for c in cols if c in telemetry.columns]]
```

- [ ] **Step 4: Run both tests to verify they pass**

```bash
python -m pytest tests/test_data_loader.py -v 2>&1 | tail -10
```
Expected: all data_loader tests pass

- [ ] **Step 5: Commit**

```bash
git add data_loader.py tests/test_data_loader.py
git commit -m "feat: add multi-lap support to get_driver_telemetry()"
```

---

### Task 3: Update `extract_features()` for multi-lap + weather

**Files:**
- Modify: `feature_engineering.py`
- Test: `tests/test_feature_engineering.py`

**Interfaces:**
- Consumes: `extract_features(driver_telemetry_dict, laps="fastest", weather_dict=None)`
- Produces: Feature DataFrame with 5 base columns (+ possibly 10 mean/std columns + 3 weather columns)

- [ ] **Step 1: Add tests for multi-lap and weather features**

Add to `tests/test_feature_engineering.py`:

```python
def test_extract_features_multilap(self):
    session = dl.load_session(2023, "Bahrain", "R")
    telemetry = {"VER": dl.get_driver_telemetry(session, "VER", laps="all"),
                 "PER": dl.get_driver_telemetry(session, "PER", laps="all")}
    features = fe.extract_features(telemetry, laps="all")
    assert "mean_speed_mean" in features.columns
    assert "mean_speed_std" in features.columns
    assert "lap_count" in features.columns
    assert features.loc["VER", "lap_count"] > 1
    assert len(features.columns) == 11  # 5 mean + 5 std + lap_count

def test_extract_features_weather(self):
    session = dl.load_session(2023, "Bahrain", "R")
    telemetry = {"VER": dl.get_driver_telemetry(session, "VER")}
    weather = dl.get_weather(session)
    features = fe.extract_features(telemetry, weather_dict=weather)
    assert "track_temp" in features.columns
    assert "air_temp" in features.columns
    assert "rainfall" in features.columns
    assert features.loc["VER", "rainfall"] in (0, 1)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_feature_engineering.py -v 2>&1 | tail -10
```
Expected: new tests fail (no `laps` param on `extract_features`, missing columns)

- [ ] **Step 3: Replace `extract_features()`**

```python
import numpy as np

def extract_features(
    driver_telemetry_dict: Dict[str, pd.DataFrame],
    laps: str = "fastest",
    weather_dict: dict = None,
) -> pd.DataFrame:
    """Build a feature matrix from per-driver telemetry DataFrames.

    Args:
        driver_telemetry_dict: dict of driver_code -> telemetry DataFrame.
        laps: "fastest" (5 base features) or "all" (per-lap mean/std + lap_count).
        weather_dict: optional dict with track_temp, air_temp, rainfall.

    Returns:
        DataFrame indexed by driver code.
    """
    rows = []
    for driver, telemetry in driver_telemetry_dict.items():
        gear_col = "nGear" if "nGear" in telemetry.columns else "Gear"

        if laps == "all" and "LapNumber" in telemetry.columns:
            lap_features = []
            for lap_num, lap_data in telemetry.groupby("LapNumber"):
                mean_speed = lap_data["Speed"].mean()
                mean_throttle = lap_data["Throttle"].mean()
                brake_freq = lap_data["Brake"].mean()
                lap_features.append({
                    "mean_speed": mean_speed,
                    "mean_throttle": mean_throttle,
                    "brake_frequency": brake_freq,
                    "aggression_index": (mean_throttle * brake_freq) / max(mean_speed, 1),
                    "mean_gear": lap_data[gear_col].mean(),
                })
            lap_df = pd.DataFrame(lap_features)
            row = {
                "mean_speed_mean": lap_df["mean_speed"].mean(),
                "mean_speed_std": lap_df["mean_speed"].std(ddof=0),
                "mean_throttle_mean": lap_df["mean_throttle"].mean(),
                "mean_throttle_std": lap_df["mean_throttle"].std(ddof=0),
                "brake_frequency_mean": lap_df["brake_frequency"].mean(),
                "brake_frequency_std": lap_df["brake_frequency"].std(ddof=0),
                "aggression_index_mean": lap_df["aggression_index"].mean(),
                "aggression_index_std": lap_df["aggression_index"].std(ddof=0),
                "mean_gear_mean": lap_df["mean_gear"].mean(),
                "mean_gear_std": lap_df["mean_gear"].std(ddof=0),
                "lap_count": len(lap_df),
            }
        else:
            mean_speed = telemetry["Speed"].mean()
            mean_throttle = telemetry["Throttle"].mean()
            brake_freq = telemetry["Brake"].mean()
            row = {
                "mean_speed": mean_speed,
                "mean_throttle": mean_throttle,
                "brake_frequency": brake_freq,
                "aggression_index": (mean_throttle * brake_freq) / max(mean_speed, 1),
                "mean_gear": telemetry[gear_col].mean(),
            }

        if weather_dict:
            row["track_temp"] = weather_dict.get("track_temp", 0.0)
            row["air_temp"] = weather_dict.get("air_temp", 0.0)
            row["rainfall"] = 1 if weather_dict.get("rainfall", False) else 0

        rows.append(row)

    return pd.DataFrame(rows, index=list(driver_telemetry_dict.keys()))
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_feature_engineering.py -v 2>&1 | tail -10
```
Expected: all feature_engineering tests pass

- [ ] **Step 5: Commit**

```bash
git add feature_engineering.py tests/test_feature_engineering.py
git commit -m "feat: add multi-lap and weather features to extract_features()"
```

---

### Task 4: Update report with weather + lap count

**Files:**
- Modify: `report.py`
- Test: `tests/test_report.py`

**Interfaces:**
- Consumes: `generate_report(feature_df, style_labels, sector_times_dict, weather_dict=None)`
- Produces: Formatted report string including weather and lap count

- [ ] **Step 1: Add test for weather + lap count in report**

Add to `tests/test_report.py`:

```python
def test_report_weather_multilap(self):
    df = self.feature_df.copy()
    df["track_temp"] = 32.5
    df["air_temp"] = 28.3
    df["rainfall"] = 0
    df["lap_count"] = 57
    report = rp.generate_report(df, ["Aggressive"], self.sector_dict, weather_dict={
        "track_temp": 32.5, "air_temp": 28.3, "rainfall": False
    })
    assert "Track Temp" in report
    assert "Air Temp" in report
    assert "Rainfall" in report
    assert "Laps Analyzed" in report
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_report.py::TestReport::test_report_weather_multilap -v
```
Expected: FAIL (generate_report doesn't accept `weather_dict`)

- [ ] **Step 3: Update `generate_report()`**

Replace the function:

```python
def generate_report(
    feature_df: pd.DataFrame,
    style_labels: List[str],
    sector_times_dict: Dict[str, Tuple[float, float, float]],
    weather_dict: dict = None,
) -> str:
    """Generate a formatted text report summarizing driver styles and performance."""
    lines = ["=" * 50, "F1 DRIVER ANALYSIS REPORT", "=" * 50, ""]
    for i, driver in enumerate(feature_df.index):
        lines.append(f"Driver: {driver}")
        lines.append(f"  Style Classification: {style_labels[i]}")
        
        # Multi-lap features take precedence if present
        if "mean_speed_mean" in feature_df.columns:
            lines.append(f"  Mean Speed: {feature_df.loc[driver, 'mean_speed_mean']:.1f} km/h")
            lines.append(f"  Speed Std Dev: {feature_df.loc[driver, 'mean_speed_std']:.1f} km/h")
            lines.append(f"  Brake Frequency: {feature_df.loc[driver, 'brake_frequency_mean']:.3f}")
            lines.append(f"  Aggression Index: {feature_df.loc[driver, 'aggression_index_mean']:.3f}")
        else:
            lines.append(f"  Mean Speed: {feature_df.loc[driver, 'mean_speed']:.1f} km/h")
            lines.append(f"  Brake Frequency: {feature_df.loc[driver, 'brake_frequency']:.3f}")
            lines.append(f"  Aggression Index: {feature_df.loc[driver, 'aggression_index']:.3f}")
        
        if driver in sector_times_dict:
            s1, s2, s3 = sector_times_dict[driver]
            lines.append(f"  Sector Times: {s1:.2f}s / {s2:.2f}s / {s3:.2f}s")
        
        if "lap_count" in feature_df.columns:
            lines.append(f"  Laps Analyzed: {int(feature_df.loc[driver, 'lap_count'])}")
        
        lines.append("")
    
    # Weather section (appears once, not per driver)
    if weather_dict:
        lines.append("---")
        lines.append("Session Conditions:")
        lines.append(f"  Track Temp: {weather_dict.get('track_temp', 0):.1f}°C")
        lines.append(f"  Air Temp: {weather_dict.get('air_temp', 0):.1f}°C")
        lines.append(f"  Rainfall: {'Yes' if weather_dict.get('rainfall', False) else 'No'}")
        lines.append("")
    
    lines.append("=" * 50)
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_report.py -v 2>&1 | tail -10
```
Expected: all report tests pass

- [ ] **Step 5: Commit**

```bash
git add report.py tests/test_report.py
git commit -m "feat: add weather and lap count to report"
```

---

### Task 5: Update `server/main.py` to pass weather + use all laps

**Files:**
- Modify: `server/main.py`

- [ ] **Step 1: Update the analysis endpoint**

Replace the analysis section in `server/main.py` from the `run_analysis()` function. Change the telemetry loading to use `laps="all"` and fetch weather:

Find the `run_analysis()` function and update the telemetry loading + analysis section:

```python
@app.post("/sessions/{session_id}/analyze")
def run_analysis(session_id: str, req: AnalyzeRequest):
    session = _get_session(session_id)

    telemetry_dict = {}
    sector_dict = {}
    for code in req.driver_codes:
        code = code.upper()
        try:
            telemetry_dict[code] = dl.get_driver_telemetry(session, code, laps="all")
            sector_dict[code] = dl.get_sector_times(session, code)
        except dl.DriverNotFound:
            raise HTTPException(status_code=404, detail=f"Driver '{code}' not found")

    weather_dict = dl.get_weather(session)
    feature_df = fe.extract_features(telemetry_dict, laps="all", weather_dict=weather_dict)
    style_labels, _ = cl.perform_clustering(feature_df, n_clusters=3)

    label_map = {0: "Aggressive", 1: "Smooth Cornering", 2: "Late Braker"}
    style_names = [label_map.get(l, "Unknown") for l in style_labels]

    # Lap time prediction
    predictions = {}
    try:
        target_times = {}
        for code in req.driver_codes:
            code = code.upper()
            fastest = session.laps.pick_drivers(code).pick_fastest()
            target_times[code] = fastest["LapTime"].total_seconds()
        target_series = feature_df.index.to_series().map(target_times)
        model_pack = pr.train_lap_time_predictor(feature_df, target_series)
        predictions = {
            code: pr.predict_lap_time(model_pack, feature_df.loc[code].tolist())
            for code in req.driver_codes
        }
    except Exception:
        predictions = {}

    report_text = rp.generate_report(feature_df, style_names, sector_dict, weather_dict=weather_dict)

    vis.generate_all_visualizations(telemetry_dict, sector_dict, feature_df, style_names)

    analysis_id = str(uuid.uuid4())
    analyses[analysis_id] = {
        "report": report_text,
        "session_id": session_id,
        "driver_codes": req.driver_codes,
        "plot_names": ["speed_trace", "throttle_brake", "sector_comparison", "radar_chart", "cluster_scatter"],
    }

    return {
        "status": "ok",
        "data": {
            "analysis_id": analysis_id,
            "styles": dict(zip(req.driver_codes, style_names)),
            "predictions": predictions,
            "features": feature_df.to_dict(orient="index"),
        },
    }
```

- [ ] **Step 2: Run API tests**

```bash
python -m pytest tests/test_api.py -v 2>&1 | tail -10
```
Expected: all tests pass

- [ ] **Step 3: Run all tests**

```bash
python -m pytest tests/ -v 2>&1 | tail -15
```
Expected: 22+ tests pass (19 original + 3 new)

- [ ] **Step 4: Commit**

```bash
git add server/main.py
git commit -m "feat: integrate weather and multi-lap features into analysis endpoint"
```

---

### Task 6: Integration smoke test

- [ ] **Step 1: Start backend**

```bash
lsof -ti:8080 | xargs kill -9 2>/dev/null
uvicorn server.main:app --host 0.0.0.0 --port 8080 &
sleep 3
curl -s http://127.0.0.1:8080/sessions
```

- [ ] **Step 2: Load session and run analysis**

```bash
SID=$(curl -s -X POST http://127.0.0.1:8080/sessions/load \
  -H 'Content-Type: application/json' \
  -d '{"year": 2023, "grand_prix": "Bahrain", "session_type": "R"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['session_id'])")
echo "Session: $SID"

AID=$(curl -s -X POST "http://127.0.0.1:8080/sessions/${SID}/analyze" \
  -H 'Content-Type: application/json' \
  -d '{"driver_codes": ["VER", "PER", "ALO"]}' | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['analysis_id'])")
echo "Analysis: $AID"
```

- [ ] **Step 3: Verify features include new columns**

```bash
curl -s "http://127.0.0.1:8080/analysis/${AID}/report" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['report'])"
```
Expected: report shows weather conditions and lap count per driver

- [ ] **Step 4: Verify plots still generate**

```bash
ls -la output/*.png
curl -s "http://127.0.0.1:8080/analysis/${AID}/plots"
```
Expected: 5 PNGs, all plots listed

- [ ] **Step 5: Clean up**

```bash
lsof -ti:8080 | xargs kill -9 2>/dev/null
```
