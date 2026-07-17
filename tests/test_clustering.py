import pytest
import pandas as pd
import numpy as np
from clustering import perform_clustering, perform_pca


def make_dummy_features():
    return pd.DataFrame({
        "mean_speed": [200, 180, 220, 190, 210],
        "mean_throttle": [50, 40, 60, 45, 55],
        "brake_frequency": [0.3, 0.5, 0.2, 0.4, 0.1],
        "aggression_index": [0.1, 0.2, 0.05, 0.15, 0.08],
        "mean_gear": [6, 5, 7, 5, 6],
    }, index=["VER", "HAM", "LEC", "NOR", "ALO"])


class TestClustering:
    def test_perform_clustering_returns_labels_and_model(self):
        feature_df = make_dummy_features()
        labels, model = perform_clustering(feature_df, n_clusters=3)
        assert len(labels) == len(feature_df)
        assert hasattr(model, "labels_")

    def test_perform_clustering_labels_are_integers(self):
        feature_df = make_dummy_features()
        labels, _ = perform_clustering(feature_df, n_clusters=3)
        assert all(isinstance(l, (int, np.integer)) for l in labels)

    def test_perform_pca_returns_two_components(self):
        feature_df = make_dummy_features()
        X_pca, model = perform_pca(feature_df, n_components=2)
        assert X_pca.shape == (len(feature_df), 2)
        assert hasattr(model, "components_")
