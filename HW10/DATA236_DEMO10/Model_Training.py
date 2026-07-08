# train_iris_model.py

from sklearn.datasets import load_iris
from sklearn.neighbors import KNeighborsClassifier
import pickle

# Load dataset
iris = load_iris()

X = iris.data
y = iris.target

# Train model
model = KNeighborsClassifier(n_neighbors=3)
model.fit(X, y)

# Save model
with open("iris_knn_model.pkl", "wb") as f:
    pickle.dump(model, f)

# Save metadata
metadata = {
    "feature_names": iris.feature_names,
    "target_names": iris.target_names
}

with open("iris_metadata.pkl", "wb") as f:
    pickle.dump(metadata, f)

print("Model and metadata saved successfully!")