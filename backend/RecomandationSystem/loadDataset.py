import pandas as pd
from sklearn.preprocessing import StandardScaler
from RecomandationSystem.KNNClasification import get_or_train_model
from RecomandationSystem.KMeansClasification import find_optimal_k_hybrid
import kagglehub
from sklearn.cluster import KMeans
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
users_data_location='RecomandationSystem/data/users_data.csv'
scaler_path="scaler_hybrid.joblib"
kmeans_model_location="kmeans_hybrid_model.joblib"
transaction_data_location='RecomandationSystem/data/transactions_data_categorized.csv'
mcc_groups = {
    "Food & Dining": ["5812", "5814", "5813", "5499", "5921", "5411"],
    "Shopping & Retail": ["5311", "5310", "5300", "5661", "5977", "5655", "5651", "5621", "5947", "5941",
                          "5733", "5942", "5193", "5192", "5932", "5970", "3132", "3260"],
    "Health & Wellness": ["8099", "5912", "8021", "7230", "8041", "8011", "8043", "8049", "8062"],
    "Transportation": ["5541", "4784", "4121", "7538", "4111", "7542", "4112", "4131", "7531", "7549", "5533"],
    "Utilities & Services": ["4900", "4814", "4899", "7349", "7210", "7393", "8111", "8931", "7276", "9402", "1711", "4829"],
    "Entertainment & Travel": ["7996", "7832", "7922", "3722", "4722", "7011", "4511", "4411", "7801",
                               "7802", "7995"],
    "Home & Garden": ["5211", "5719", "5251", "3504", "5712", "3174", "5261", "3144", "5722"],
    "Electronics & Tech": ["3780", "5815", "5045", "3684", "5732", "5816"],
    "Industrial & Business": ["3390", "3596", "3730", "3775", "4214", "3509", "3640", "3771",
                              "5094", "3389", "3393", "3001", "3395", "3058", "3387", "3405", "3359", "3256", 
                              "3006", "3007", "3075", "3066", "3005", "3000", "3008", "3009", "6300"]
}

mcc_to_category = {code: cat for cat, codes in mcc_groups.items() for code in codes}
deleteColumns = ["merchant_state", "date", "merchant_city", "merchant_name", "merchant_id",
                 "use_chip","card_id","zip","mcc","errors"]
def formDataset():
    import os 
    dir_path = os.path.dirname(os.path.realpath(__file__))
    print(dir_path)
    global df
    df = pd.read_csv(os.path.join(dir_path, 'data', 'transactions_data.csv'))
    df['category'] = df['mcc'].astype(str).map(mcc_to_category).fillna("Other")
    for column in deleteColumns:
        if column in df.columns:
            df = df.drop(column, axis=1)
    df['amount'] = df['amount'].str.replace('$', '', regex=False).astype(str)
    df['amount'] = df['amount'].str.replace('-', '', regex=False).astype(float)
    
    df.to_csv(os.path.join(dir_path, 'data', 'transactions_data_categorized.csv'), index=False)
def loadDataset(user_id):
    #formDataset()
    global df
    df = pd.read_csv(transaction_data_location)
    return tran_recommandation_models(user_id)
def get_KMeans_recommandations(user_vector):
    scaler = joblib.load(scaler_path) 
    scaled_vector = scaler.transform(user_vector)
    kmeans = joblib.load(kmeans_model_location)
    predicted_cluster = kmeans.predict(scaled_vector)[0]
    similar_users = matrix[matrix['cluster_id'] == predicted_cluster].index.tolist()
    return similar_users
def tran_recommandation_models(user_id=461):
    global df, matrix,unscaled_pivot_matrix

    user_category_matrix = df.pivot_table(
        index='client_id', 
        columns='category', 
        values='amount', 
        aggfunc='sum'
    ).fillna(0)
    unscaled_pivot_matrix = user_category_matrix.copy()
    users_df = pd.read_csv(users_data_location)
    credit_scores = users_df.set_index('id')['credit_score']
    matrix_with_credit = user_category_matrix.join(credit_scores, how='inner')
    #find_optimal_k_hybrid(matrix_with_credit)
    scaler = StandardScaler()
    matrix_scaled_values = scaler.fit_transform(matrix_with_credit)
    joblib.dump(scaler, scaler_path)
    matrix_final = pd.DataFrame(
        matrix_scaled_values, 
        index=matrix_with_credit.index, 
        columns=matrix_with_credit.columns
    )
    model_knn, matrix_final = get_or_train_model(matrix_final)
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    matrix_final['cluster_id'] = kmeans.fit_predict(matrix_final.values)
    joblib.dump(kmeans, kmeans_model_location)
    matrix = matrix_final 
    return matrix_final
recommendable_categories = [
        "Music Stores - Musical Instruments", "Sporting Goods Stores", "Airlines", 
        "Digital Goods - Games", "Precious Stones and Metals", 
        "Furniture, Home Furnishings, and Equipment Stores", "Book Stores",
        "Amusement Parks, Carnivals, Circuses", "Eating Places and Restaurants", 
        "Fast Food Restaurants", "Discount Stores", "Taxicabs and Limousines", 
        "Miscellaneous Home Furnishing Stores", "Motion Picture Theaters", 
        "Shoe Stores", "Cosmetic Stores", "Digital Goods - Media, Books, Apps"
    ]
def print_neighbor_spending_from_df(neighbor_ids):
    """
    neighbor_ids: list of IDs returned by KNN
    Loads the RAW transaction data to access the 'mcc' column for detailed categorization.
    """
    # We do NOT use the global df here because it lacks the 'mcc' column.

    # 1. Load the JSON categories
    json_path = os.path.join('RecomandationSystem', 'data', 'mcc_codes.json')
    try:
        with open(json_path, 'r') as f:
            mcc_categories = json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_path} not found.")
        return

    # 2. Load Credit Scores
    users_path = os.path.join('RecomandationSystem', 'data', 'users_data.csv')
    if not os.path.exists(users_path):
        print(f"Error: {users_path} not found.")
        return
    users_df = pd.read_csv(users_path)
    credit_map = users_df.set_index('id')['credit_score'].to_dict()

    # 3. Load the RAW transaction data (which still has the 'mcc' column)
    # Adjust this path if your raw data file is named differently or located elsewhere.
    raw_data_path = os.path.join('RecomandationSystem', 'data', 'transactions_data.csv')
    if not os.path.exists(raw_data_path):
         print(f"Error: Raw data file {raw_data_path} not found. Cannot perform detailed MCC analysis.")
         return
         
    # To optimize memory, we only load the columns we need
    try:
        raw_df = pd.read_csv(raw_data_path, usecols=['client_id', 'mcc', 'amount'])
    except ValueError as e:
        print(f"Error loading raw data: {e}. Check if 'client_id', 'mcc', and 'amount' exist in {raw_data_path}.")
        return
    print("\n--- Sample of Raw Transactions for Neighbors ---")
    print(raw_df[raw_df['client_id'] == 192].head())
    # 4. Filter the raw data for our specific neighbors
    temp_df = raw_df[raw_df['client_id'].isin(neighbor_ids)].copy()
    if temp_df.empty:
        print("\nNo detailed transactions found for these neighbors in the raw dataset.")
        return
    
    temp_df['amount'] = temp_df['amount'].str.replace('$', '', regex=False).astype(str)
    temp_df['amount'] = temp_df['amount'].str.replace('-', '', regex=False).astype(float)

    # Force conversion to a standard float64 (NumPy backed, not Arrow backed)
    # This prevents the Arrow string array error during unstack
    
    temp_df['amount'] = pd.to_numeric(temp_df['amount'], errors='coerce').astype('float64')
    

    # Map the MCC to the extended category
    temp_df['extended_category'] = temp_df['mcc'].astype(str).map(mcc_categories).fillna("Other/Unknown")
    
    # 6. Aggregate
    # Drop NA values that might have been created by coercion just to be safe
    clean_temp_df = temp_df.dropna(subset=['amount'])
    
    spending_summary = clean_temp_df.groupby(['client_id', 'extended_category'])['amount'].sum().unstack(fill_value=0.0)
    # 7. Print Output
    print("\n" + "="*75)
    print("DETAILED ANALYSIS: Neighbor Profiles (Source: mcc_codes.json)")
    print("="*75)

    for neighbor_id in neighbor_ids:
        c_score = credit_map.get(neighbor_id, "N/A")
        print(f"\n> SIMILAR NEIGHBOR ID: {neighbor_id} | CREDIT SCORE: {c_score}")
        print("-" * 60)

        if neighbor_id in spending_summary.index:
            user_spending = spending_summary.loc[neighbor_id].sort_values(ascending=False)
            
            for cat, amt in user_spending.items():
                if amt > 0:
                    print(f"  {cat.ljust(45)}: {amt:10.2f} USD")
        else:
            print("  (!) Transaction data missing for this ID.")
        print("-" * 60)
def get_mcc_and_transactions():
    mcc_path = os.path.join('RecomandationSystem', 'data', 'mcc_codes.json')
    try:
        with open(mcc_path, 'r') as f:
            mcc_categories = json.load(f)
    except FileNotFoundError:
        print("Eroare: mcc_codes.json nu a fost găsit.")
        return []

    raw_data_path = os.path.join('RecomandationSystem', 'data', 'transactions_data.csv')
    try:
        raw_df = pd.read_csv(raw_data_path, usecols=['client_id', 'mcc', 'amount'])
    except Exception as e:
        print(f"Eroare la citirea datelor brute: {e}")
        return []
    return mcc_categories, raw_df
def clean_data_for_recommendations(temp_df):
    temp_df['amount'] = temp_df['amount'].str.replace('$', '', regex=False).astype(str)
    temp_df['amount'] = temp_df['amount'].str.replace('-', '', regex=False).astype(float)
    temp_df['amount'] = pd.to_numeric(temp_df['amount'], errors='coerce').astype('float64')
    return temp_df
def generate_category_recommendations(target_user_id, neighbor_ids):
    mcc_categories, raw_df = get_mcc_and_transactions()
    all_relevant_ids = [target_user_id] + neighbor_ids
    temp_df = raw_df[raw_df['client_id'].isin(all_relevant_ids)].copy()
    if temp_df.empty:
        return []
    temp_df = clean_data_for_recommendations(temp_df)
    temp_df['detailed_category'] = temp_df['mcc'].astype(str).map(mcc_categories).fillna("Other/Unknown")
    pivot_df = temp_df.groupby(['client_id', 'detailed_category'])['amount'].sum().unstack(fill_value=0.0)
    if target_user_id in pivot_df.index:
        target_profile = pivot_df.loc[target_user_id]
    else:
        target_profile = pd.Series(dtype=float)
    valid_neighbors = pivot_df.index.intersection(neighbor_ids)
    if valid_neighbors.empty:
        return []
    neighbors_profiles = pivot_df.loc[valid_neighbors]
    neighbors_avg = neighbors_profiles.mean()
    recommendations = {}
    for category in recommendable_categories:
        if category in neighbors_avg.index:
            avg_neighbor_spend = neighbors_avg[category]
            target_user_spend = target_profile.get(category, 0.0)
            score = avg_neighbor_spend - target_user_spend
            if score > 0:
                recommendations[category] = score
    top_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[:3]
    return [cat for cat, score in top_recommendations]
