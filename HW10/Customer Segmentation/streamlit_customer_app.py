import streamlit as st
import pickle
import numpy as np
import matplotlib.pyplot as plt
import os

MODEL_FILE = "customer_kmeans_model_kruthika.pkl"
METADATA_FILE = "customer_metadata.pkl"

@st.cache_resource
def load_resources(model_file, metadata_file):
    if not os.path.exists(model_file) or not os.path.exists(metadata_file):
        st.error("Model files not found. Please run 'train_customer_model.py' first!")
        return None, None
    with open(model_file, "rb") as f:
        model = pickle.load(f)
    with open(metadata_file, "rb") as f:
        metadata = pickle.load(f)
    return model, metadata

model, metadata = load_resources(MODEL_FILE, METADATA_FILE)

st.title("Customer Segmentation")
st.markdown("Predict which customer segment a person belongs to based on their profile.")

if model is not None:
    feature_names = metadata["feature_names"]
    X_train = metadata["X_train"]
    cluster_centers = metadata["cluster_centers"]

    st.sidebar.header("Customer Profile")
    annual_income = st.sidebar.slider(feature_names[0], 15.0, 137.0, 70.0, 1.0)
    spending_score = st.sidebar.slider(feature_names[1], 1.0, 99.0, 50.0, 1.0)

    input_features = np.array([[annual_income, spending_score]])
    predicted_cluster = model.predict(input_features)[0]

    st.metric(label="Predicted Cluster ID", value=int(predicted_cluster))

    colors = ["#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4"]
    cluster_labels = model.labels_

    fig, ax = plt.subplots(figsize=(9, 6))

    for c in range(5):
        mask = cluster_labels == c
        ax.scatter(
            X_train[mask, 0], X_train[mask, 1],
            c=colors[c], label=f"Cluster {c}", alpha=0.6, s=50
        )

    ax.scatter(
        cluster_centers[:, 0], cluster_centers[:, 1],
        c="black", marker="X", s=200, zorder=5, label="Centroids"
    )

    ax.scatter(
        annual_income, spending_score,
        c="yellow", edgecolors="black", marker="*", s=400, zorder=6,
        label=f"Your Customer (Cluster {int(predicted_cluster)})"
    )

    ax.set_xlabel(feature_names[0])
    ax.set_ylabel(feature_names[1])
    ax.set_title("Customer Segments — K-Means (k=5)")
    ax.legend(loc="upper right", fontsize=8)

    st.pyplot(fig)

    st.subheader("Input Summary")
    st.table({
        feature_names[0]: [f"{annual_income:.1f} k$"],
        feature_names[1]: [f"{spending_score:.1f}"],
        "Assigned Cluster": [int(predicted_cluster)]
    })
