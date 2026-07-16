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
