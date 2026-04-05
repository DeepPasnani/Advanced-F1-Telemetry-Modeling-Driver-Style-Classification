"""
Clustering module for driver style classification.

This module provides functions to:
- Cluster drivers using KMeans or Agglomerative Hierarchical Clustering
- Assign style labels based on cluster centroid analysis
- Generate cluster summary

The clustering labels:
- "Late Braker": highest mean_speed
- "Smooth Cornering": middle characteristics
- "Aggressive": highest aggression_index
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.decomposition import PCA
from typing import Tuple, List


def cluster_drivers(feature_df: pd.DataFrame, method: str = "kmeans") -> np.ndarray:
    """
    Cluster drivers using KMeans or Agglomerative Hierarchical Clustering.

    Args:
        feature_df: DataFrame with driver features
        method: 'kmeans' or 'agglomerative'

    Returns:
        Array of cluster labels
    """
    if len(feature_df) < 3:
        n_clusters = len(feature_df)
    else:
        n_clusters = 3
    
    feature_columns = ["mean_speed", "max_speed", "mean_throttle", "brake_frequency",
                       "mean_rpm", "mean_gear", "aggression_index"]
    
    available_columns = [col for col in feature_columns if col in feature_df.columns]
    
    if not available_columns:
        return np.zeros(len(feature_df), dtype=int)
    
    X = feature_df[available_columns].values
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    if method == "kmeans":
        model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    else:
        model = AgglomerativeClustering(n_clusters=n_clusters)
    
    labels = model.fit_predict(X_scaled)
    
    return labels


def assign_style_labels(feature_df: pd.DataFrame, labels: np.ndarray) -> List[str]:
    """
    Map cluster IDs to style names based on centroid analysis.

    Style assignment logic:
    - Highest aggression_index -> "Aggressive"
    - Highest mean_speed -> "Late Braker"
    - Else -> "Smooth Cornering"

    Args:
        feature_df: DataFrame with driver features
        labels: Cluster labels from clustering

    Returns:
        List of style labels for each driver
    """
    if len(feature_df) == 0:
        return []
    
    feature_columns = ["mean_speed", "max_speed", "mean_throttle", "brake_frequency",
                       "mean_rpm", "mean_gear", "aggression_index"]
    available_columns = [col for col in feature_columns if col in feature_df.columns]
    
    if not available_columns:
        return ["Smooth Cornering"] * len(feature_df)
    
    X = feature_df[available_columns].values
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    unique_labels = np.unique(labels)
    
    cluster_stats = {}
    for label in unique_labels:
        cluster_mask = labels == label
        cluster_mean = X_scaled[cluster_mask].mean(axis=0)
        
        aggression_idx_col = available_columns.index("aggression_index") if "aggression_index" in available_columns else -1
        speed_idx_col = available_columns.index("mean_speed") if "mean_speed" in available_columns else -1
        
        aggression_val = cluster_mean[aggression_idx_col] if aggression_idx_col >= 0 else 0
        speed_val = cluster_mean[speed_idx_col] if speed_idx_col >= 0 else 0
        
        cluster_stats[label] = {
            "aggression_index": aggression_val,
            "mean_speed": speed_val,
            "centroid": cluster_mean
        }
    
    aggression_values = [cluster_stats[l]["aggression_index"] for l in unique_labels]
    speed_values = [cluster_stats[l]["mean_speed"] for l in unique_labels]
    
    max_aggression_label = unique_labels[np.argmax(aggression_values)]
    max_speed_label = unique_labels[np.argmax(speed_values)]
    
    style_map = {}
    for label in unique_labels:
        if label == max_aggression_label:
            style_map[label] = "Aggressive"
        elif label == max_speed_label:
            style_map[label] = "Late Braker"
        else:
            style_map[label] = "Smooth Cornering"
    
    style_labels = [style_map[l] for l in labels]
    
    return style_labels


def get_cluster_summary(feature_df: pd.DataFrame, style_labels: List[str]) -> pd.DataFrame:
    """
    Get cluster summary with driver and style label information.

    Args:
        feature_df: DataFrame with driver features
        style_labels: List of style labels

    Returns:
        DataFrame with driver, cluster, and style columns
    """
    if len(feature_df) == 0:
        return pd.DataFrame()
    
    summary = feature_df.copy()
    summary["style"] = style_labels
    
    return summary


def perform_pca(feature_df: pd.DataFrame) -> Tuple[np.ndarray, PCA]:
    """
    Perform PCA for 2D visualization.

    Args:
        feature_df: DataFrame with driver features

    Returns:
        Tuple of (transformed_2d_features, pca_model)
    """
    feature_columns = ["mean_speed", "max_speed", "mean_throttle", "brake_frequency",
                       "mean_rpm", "mean_gear", "aggression_index"]
    available_columns = [col for col in feature_columns if col in feature_df.columns]
    
    if not available_columns:
        return np.zeros((len(feature_df), 2)), None
    
    X = feature_df[available_columns].values
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    return X_pca, pca


def get_kmeans_labels(feature_df: pd.DataFrame) -> np.ndarray:
    """Get KMeans cluster labels."""
    return cluster_drivers(feature_df, method="kmeans")


def get_hierarchical_labels(feature_df: pd.DataFrame) -> np.ndarray:
    """Get Agglomerative Hierarchical cluster labels."""
    return cluster_drivers(feature_df, method="agglomerative")