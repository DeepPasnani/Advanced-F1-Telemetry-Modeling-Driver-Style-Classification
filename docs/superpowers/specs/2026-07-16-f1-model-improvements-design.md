# F1 Model Improvements — Phase 3 Design

## Overview

Enhance the existing telemetry analysis pipeline with two targeted improvements:
1. **Weather-aware features** — incorporate track/air temperature and rainfall
2. **Multi-lap aggregation** — use all laps per driver, not just the fastest

Both bolt into the existing feature extraction without changing the API contract.

## Changes Required

### 1. `data_loader.py`

**New function:**
```python
def get_weather(session) -> dict
```
Returns `{"track_temp": float, "air_temp": float, "rainfall": bool}` averaged over the session duration from `session.weather_data`.

FastF1's `session.weather_data` is a DataFrame with columns: Time, AirTemp, TrackTemp, Humidity, Pressure, WindSpeed, Rainfall. We take the mean of numeric columns and the mode of Rainfall (any rain → True).

**Modified function:**
```python
def get_driver_telemetry(session, driver_code, laps="fastest") -> DataFrame
```
- `laps="fastest"` → current behavior (fastest lap only)
- `laps="all"` → concatenates telemetry from all completed laps for that driver

### 2. `feature_engineering.py`

**New features in `extract_features()`:**

Per-lap statistics (when `laps="all"`):
- `mean_speed_mean`, `mean_speed_std`
- `mean_throttle_mean`, `mean_throttle_std`
- `brake_frequency_mean`, `brake_frequency_std`
- `aggression_index_mean`, `aggression_index_std`
- `mean_gear_mean`, `mean_gear_std`
- `lap_count` — number of laps completed

Weather features (when `weather_dict` provided):
- `track_temp`
- `air_temp`
- `rainfall` (0/1)

**Signature change:**
```python
def extract_features(driver_telemetry_dict, laps="fastest", weather_dict=None) -> DataFrame
```

### 3. Downstream consumers

- `clustering.py` — no changes (works on any feature matrix)
- `prediction.py` — no changes (works on any feature matrix)
- `report.py` — add weather info and lap count to report text
- `visualization.py` — no changes needed
- `server/main.py` — no API changes. Weather is fetched automatically. Multi-lap can default to True for more robust features.

### 4. `report.py`

Append to each driver section:
```
  Track Temp: 32.5°C
  Air Temp: 28.3°C
  Rainfall: No
  Laps Analyzed: 57
```

## API Impact

No new endpoints. Existing `POST /sessions/{id}/analyze` automatically fetches weather and uses all laps. The feature matrix returned in the response grows by ~13 columns.

## Testing

| Test | What it covers |
|------|---------------|
| `test_get_weather` | Returns expected keys, numeric types, rainfall bool |
| `test_get_telemetry_all_laps` | Returns multi-lap concatenated telemetry for a driver |
| `test_extract_features_weather` | Feature matrix includes `track_temp`, `air_temp`, `rainfall` |
| `test_extract_features_multilap` | Feature matrix includes `*_mean`, `*_std`, `lap_count` columns |
| `test_report_weather_multilap` | Report output includes weather + lap count lines |

## Out of Scope

- Deep learning classifier (would need 1000+ labeled drivers, not 20)
- Real-time streaming (WebSocket server, different project)
- Steering / DRS / ERS data (FastF1 has it, add when someone asks)

## File Changes Summary

| File | Change |
|------|--------|
| `data_loader.py` | Add `get_weather()`, extend `get_driver_telemetry()` with `laps` param |
| `feature_engineering.py` | Add weather + multi-lap features |
| `report.py` | Include weather + lap count in output |
| `tests/test_data_loader.py` | +2 tests |
| `tests/test_feature_engineering.py` | +2 tests |
| `tests/test_report.py` | +1 test |
| `clustering.py` | Unchanged |
| `prediction.py` | Unchanged |
| `visualization.py` | Unchanged |
| `server/main.py` | Unchanged |
