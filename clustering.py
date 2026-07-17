"""
Clustering module for F1 driver style classification.
Uses KMeans and PCA from scikit-learn.
"""

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


def perform_pca(feature_df, n_components: int = 2):
    """Reduce feature dimensions with PCA. Returns (X_pca, model)."""
    scaler = StandardScaler()
    scaled = scaler.fit_transform(feature_df.values)
    model = PCA(n_components=n_components, random_state=42)
    X_pca = model.fit_transform(scaled)
    return X_pca, model
