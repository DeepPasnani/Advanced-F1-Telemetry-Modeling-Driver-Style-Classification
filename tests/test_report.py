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

    def test_report_weather_multilap(self):
        df = pd.DataFrame({
            "mean_speed_mean": [200.0],
            "mean_speed_std": [5.0],
            "mean_throttle_mean": [50.0],
            "mean_throttle_std": [3.0],
            "brake_frequency_mean": [0.3],
            "brake_frequency_std": [0.05],
            "aggression_index_mean": [0.1],
            "aggression_index_std": [0.02],
            "mean_gear_mean": [6.0],
            "mean_gear_std": [0.5],
            "lap_count": [57],
            "track_temp": [32.5],
            "air_temp": [28.3],
            "rainfall": [0],
        }, index=["VER"])
        report = generate_report(df, ["Aggressive"], {"VER": (30.0, 35.0, 28.0)},
                                 weather_dict={"track_temp": 32.5, "air_temp": 28.3, "rainfall": False})
        assert "Track Temp" in report
        assert "Air Temp" in report
        assert "Rainfall" in report
        assert "Laps Analyzed" in report
        assert "Speed Std Dev" in report
