import pytest
import pandas as pd
from report import generate_report


def make_dummy_data():
    feature_df = pd.DataFrame({
        "mean_speed": [200, 180],
        "mean_throttle": [50, 40],
        "brake_frequency": [0.3, 0.5],
        "aggression_index": [0.1, 0.2],
        "mean_gear": [6, 5],
    }, index=["VER", "HAM"])
    styles = ["Aggressive", "Smooth Cornering"]
    sectors = {"VER": (30.0, 35.0, 28.0), "HAM": (31.0, 34.0, 29.0)}
    return feature_df, styles, sectors


class TestReport:
    def test_generate_returns_string(self):
        feature_df, styles, sectors = make_dummy_data()
        result = generate_report(feature_df, styles, sectors)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_contains_driver_names(self):
        feature_df, styles, sectors = make_dummy_data()
        result = generate_report(feature_df, styles, sectors)
        assert "VER" in result
        assert "HAM" in result

    def test_generate_contains_style_labels(self):
        feature_df, styles, sectors = make_dummy_data()
        result = generate_report(feature_df, styles, sectors)
        assert "Aggressive" in result
        assert "Smooth Cornering" in result
