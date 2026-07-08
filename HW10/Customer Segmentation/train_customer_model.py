import numpy as np
import pickle
from sklearn.cluster import KMeans

np.random.seed(42)

annual_income = np.random.uniform(15, 137, 200)
spending_score = np.random.uniform(1, 99, 200)
X = np.column_stack([annual_income, spending_score])

model = KMeans(n_clusters=5, random_state=42, n_init=10)
model.fit(X)

with open("customer_kmeans_model_kruthika.pkl", "wb") as f:
    pickle.dump(model, f)

metadata = {
    "feature_names": ["Annual Income (k$)", "Spending Score (1-100)"],
    "cluster_centers": model.cluster_centers_,
    "X_train": X
}

with open("customer_metadata.pkl", "wb") as f:
    pickle.dump(metadata, f)

print("Model saved to customer_kmeans_model_kruthika.pkl")
print("Metadata saved to customer_metadata.pkl")
print(f"Cluster centers:\n{model.cluster_centers_}")
