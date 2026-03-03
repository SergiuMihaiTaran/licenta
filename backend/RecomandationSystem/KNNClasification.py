import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
import joblib
import os

MODEL_PATH = "knn_model.joblib"
MATRIX_PATH = "norm_matrix.joblib"

def get_or_train_model(user_category_matrix):
    global model, matrix
    if os.path.exists(MODEL_PATH) and os.path.exists(MATRIX_PATH):  
        model = joblib.load(MODEL_PATH)
        matrix = joblib.load(MATRIX_PATH)
    else:
        mean_user_category = np.mean(user_category_matrix.values, axis=1).reshape(-1, 1)
        normalized_values = user_category_matrix.values - mean_user_category
        normalized_matrix = pd.DataFrame(
            normalized_values, 
            index=user_category_matrix.index, 
            columns=user_category_matrix.columns
        )
        model = NearestNeighbors(metric='correlation', algorithm='brute')
        model.fit(normalized_matrix.values)
        joblib.dump(model, MODEL_PATH)
        joblib.dump(normalized_matrix, MATRIX_PATH)
        matrix = normalized_matrix
    
    return model, matrix
def get_neighbor_spending(user_spending_vector):
    global df 
    distances, indices = model.kneighbors(user_spending_vector, n_neighbors=6)
    similar_user_ids = matrix.index[indices.flatten()[1:]].tolist()
    return similar_user_ids
