import pytest
import pandas as pd
import numpy as np
from feature_engineering import extract_features


def make_dummy_telemetry(speed=200, throttle=50, brake=0.1, gear=6):
    return pd.DataFrame({
        "Distance": np.linspace(0, 5000, 100),
        "Speed": np.full(100, speed),
        "Throttle": np.full(100, throttle),
        "Brake": np.full(100, brake),
        "RPM": np.full(100, 8000),
        "Gear": np.full(100, gear),
        "nGear": np.full(100, gear),
    })


class TestFeatureEngineering:
    def test_extract_features_returns_dataframe(self):
        tele_dict = {"VER": make_dummy_telemetry(), "HAM": make_dummy_telemetry(speed=210)}
        result = extract_features(tele_dict)
        assert isinstance(result, pd.DataFrame)
        assert list(result.index) == ["VER", "HAM"]

    def test_extract_features_has_correct_columns(self):
        tele_dict = {"VER": make_dummy_telemetry()}
        result = extract_features(tele_dict)
        expected = {"mean_speed", "mean_throttle", "brake_frequency", "aggression_index", "mean_gear"}
        assert expected.issubset(result.columns)

    def test_aggression_index_value(self):
        tele_dict = {"VER": make_dummy_telemetry(speed=200, throttle=80, brake=0.5)}
        result = extract_features(tele_dict)
        expected = (80 * 0.5) / 200
        assert abs(result.loc["VER", "aggression_index"] - expected) < 0.001

    def test_extract_features_multilap(self):
        # Multiple laps with LapNumber column
        lap1 = make_dummy_telemetry(speed=200, throttle=50, brake=0.1)
        lap1["LapNumber"] = 1
        lap2 = make_dummy_telemetry(speed=210, throttle=60, brake=0.2)
        lap2["LapNumber"] = 2
        lap3 = make_dummy_telemetry(speed=190, throttle=40, brake=0.05)
        lap3["LapNumber"] = 3
        multi = pd.concat([lap1, lap2, lap3], ignore_index=True)
        tele_dict = {"VER": multi}
        features = extract_features(tele_dict, laps="all")
        assert "mean_speed_mean" in features.columns
        assert "mean_speed_std" in features.columns
        assert "lap_count" in features.columns
        assert features.loc["VER", "lap_count"] == 3
        expected_speed_mean = (200 + 210 + 190) / 3
        assert abs(features.loc["VER", "mean_speed_mean"] - expected_speed_mean) < 0.001

    def test_extract_features_weather(self):
        tele_dict = {"VER": make_dummy_telemetry()}
        weather = {"track_temp": 32.5, "air_temp": 28.3, "rainfall": False}
        features = extract_features(tele_dict, weather_dict=weather)
        assert "track_temp" in features.columns
        assert "air_temp" in features.columns
        assert "rainfall" in features.columns
        assert abs(features.loc["VER", "track_temp"] - 32.5) < 0.001
        assert abs(features.loc["VER", "air_temp"] - 28.3) < 0.001
        assert features.loc["VER", "rainfall"] == 0
