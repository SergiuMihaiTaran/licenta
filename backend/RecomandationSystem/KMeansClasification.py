import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

# Definim MODEL_PATH pentru consistență
MODEL_PATH = "kmeans_users_model.joblib"
SCALER_PATH = "scaler_users.joblib"

def find_optimal_k_hybrid(matrix_df):
    features_to_use = [col for col in matrix_df.columns if col not in ['cluster_id', 'client_id']]
    X = matrix_df[features_to_use].astype(float)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    inertia = []
    K_range = range(1, 11) 
    for k in K_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        inertia.append(km.inertia_)
    for k in [2, 3, 4, 5, 6, 7, 8]:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        score = silhouette_score(X_scaled, labels)
        print(f"Silhouette Score pentru k={k}: {score:.4f}")
    plt.figure(figsize=(8, 5))
    plt.plot(K_range, inertia, 'bx-', linewidth=2, markersize=8)
    plt.xlabel('Număr de Clustere (k)', fontsize=12)
    plt.ylabel('Inerție (SSE)', fontsize=12)
    plt.title('Metoda Elbow (9 Categorii + Credit Score)', fontsize=14)
    plt.xticks(K_range)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.show()

    

def train_model(matrix_df, n_clusters=5):
    data_for_clustering = matrix_df.astype(float)
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(data_for_clustering)
    kmeans_model = KMeans(n_clusters=n_clusters, init='k-means++', random_state=42, n_init=10)
    clustered_df = matrix_df.copy()
    clustered_df['cluster_id'] = kmeans_model.fit_predict(scaled_data)
    joblib.dump(kmeans_model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    return clustered_df, kmeans_model

def get_users_in_same_cluster(user_vector, clustered_df):
    """
    clustered_df: DataFrame returned by train_model
    """
    kmeans_model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    input_array = np.array(user_vector).reshape(1, -1)
    scaled_input = scaler.transform(input_array)
    predicted_cluster = kmeans_model.predict(scaled_input)[0]
    similar_users = clustered_df[clustered_df['cluster_id'] == predicted_cluster]
    
    return predicted_cluster, similar_users