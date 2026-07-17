import pytest
import pandas as pd
import numpy as np
from prediction import train_lap_time_predictor, predict_lap_time


def make_dummy_data():
    feature_df = pd.DataFrame({
        "mean_speed": [200, 180, 220, 190, 210],
        "mean_throttle": [50, 40, 60, 45, 55],
        "brake_frequency": [0.3, 0.5, 0.2, 0.4, 0.1],
        "aggression_index": [0.1, 0.2, 0.05, 0.15, 0.08],
        "mean_gear": [6, 5, 7, 5, 6],
    }, index=["VER", "HAM", "LEC", "NOR", "ALO"])
    target = pd.Series([90.0, 92.0, 88.0, 91.0, 89.5], index=feature_df.index)
    return feature_df, target


class TestPrediction:
    def test_train_returns_model_pack(self):
        feature_df, target = make_dummy_data()
        pack = train_lap_time_predictor(feature_df, target)
        assert "model" in pack
        assert "scaler" in pack

    def test_predict_returns_float(self):
        feature_df, target = make_dummy_data()
        pack = train_lap_time_predictor(feature_df, target)
        features = feature_df.iloc[0].values.tolist()
        pred = predict_lap_time(pack, features)
        assert isinstance(pred, (float, np.floating))
        assert pred > 0
