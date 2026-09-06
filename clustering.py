"""
Clustering module for F1 driver style classification.
Uses KMeans and PCA from scikit-learn.
"""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


def perform_clustering(feature_df, n_clusters: int = 3):
    """Cluster drivers by feature matrix using KMeans. Returns (labels, model)."""
    scaler = StandardScaler()
    scaled = scaler.fit_transform(feature_df.values)
    model = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    labels = model.fit_predict(scaled)
    return labels, model


def label_style_clusters(feature_df, labels):
    """Map KMeans cluster indices to human-readable style names.

    KMeans cluster indices are arbitrary and unstable across runs — cluster
    "0" has no inherent meaning. Instead, name each cluster from its own
    mean feature values so a label always reflects the *relative* driving
    behavior of the group it was assigned to, rather than being an artifact
    of cluster ordering:
      - the cluster with the highest mean aggression index -> "Aggressive"
      - of what remains, the highest mean brake frequency  -> "Late Braker"
      - whatever is left                                   -> "Smooth Cornering"

    Returns a list of style names aligned to `labels` (and therefore to
    `feature_df`'s row order).
    """
    labels = np.asarray(labels)
    agg_col = "aggression_index_mean" if "aggression_index_mean" in feature_df.columns else "aggression_index"
    brake_col = "brake_frequency_mean" if "brake_frequency_mean" in feature_df.columns else "brake_frequency"

    remaining = set(np.unique(labels).tolist())
    stats = {
        c: {
            "aggression": feature_df.loc[labels == c, agg_col].mean(),
            "brake": feature_df.loc[labels == c, brake_col].mean(),
        }
        for c in remaining
    }

    name_map = {}

    aggressive_cluster = max(remaining, key=lambda c: stats[c]["aggression"])
    name_map[aggressive_cluster] = "Aggressive"
    remaining.discard(aggressive_cluster)

    if remaining:
        late_braker_cluster = max(remaining, key=lambda c: stats[c]["brake"])
        name_map[late_braker_cluster] = "Late Braker"
        remaining.discard(late_braker_cluster)

    for c in remaining:
        name_map[c] = "Smooth Cornering"

    return [name_map[l] for l in labels]


def perform_pca(feature_df, n_components: int = 2):
    """Reduce feature dimensions with PCA. Returns (X_pca, model)."""
    scaler = StandardScaler()
    scaled = scaler.fit_transform(feature_df.values)
    model = PCA(n_components=n_components, random_state=42)
    X_pca = model.fit_transform(scaled)
    return X_pca, model
