
import streamlit as st
import pickle
import numpy as np
import pandas as pd
import os

# --- 1. Model and Metadata Loading (Cached) ---
MODEL_FILE = 'iris_knn_model.pkl'
METADATA_FILE = 'iris_metadata.pkl'

@st.cache_resource
def load_resources(model_file, metadata_file):
    """Loads the pickled model and metadata."""
    try:
        if not os.path.exists(model_file) or not os.path.exists(metadata_file):
            st.error("Required model or metadata files not found. Please run 'train_iris_model.py' first!")
            return None, None

        with open(model_file, 'rb') as f:
            model = pickle.load(f)
        
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
            
        return model, metadata
    except Exception as e:
        st.error(f"Error loading resources: {e}")
        return None, None

model, metadata = load_resources(MODEL_FILE, METADATA_FILE)

# --- 2. App Title and Setup ---
st.title('🌸 Iris Flower Species Classifier')
st.markdown('Predict the species of an Iris flower based on its measurements.')


if model is not None:
    # Use metadata for feature names and target names
    FEATURE_NAMES = metadata['feature_names']
    TARGET_NAMES = metadata['target_names']
    
    st.sidebar.header('Input Flower Measurements (cm)')
    
    # --- 3. User Input Widgets (Sidebar for cleanliness) ---
    # Create sliders for all 4 features
    sepal_length = st.sidebar.slider(FEATURE_NAMES[0], 4.0, 8.0, 5.4, 0.1) # Sepal Length
    sepal_width  = st.sidebar.slider(FEATURE_NAMES[1], 2.0, 4.5, 3.4, 0.1) # Sepal Width
    petal_length = st.sidebar.slider(FEATURE_NAMES[2], 1.0, 7.0, 1.3, 0.1) # Petal Length
    petal_width  = st.sidebar.slider(FEATURE_NAMES[3], 0.1, 2.5, 0.2, 0.1) # Petal Width

    # --- 4. Prediction Logic ---
    
    # Collect all inputs into the 2D array format the model expects: [[f1, f2, f3, f4]]
    input_features = np.array([[sepal_length, sepal_width, petal_length, petal_width]])

    if st.button('Predict Species'):
        # Make the prediction
        prediction_index = model.predict(input_features)[0]
        predicted_species = TARGET_NAMES[prediction_index]
        
        # Display the result
        st.subheader('Prediction Result:')
        
        # Determine color for the result based on species (optional flourish)
        species_color = {
            'setosa': 'green',
            'versicolor': 'blue',
            'virginica': 'violet'
        }.get(predicted_species, 'gray')
        
        st.markdown(
            f"The predicted species is: <h2 style='color: {species_color};'>{predicted_species.capitalize()}</h2>", 
            unsafe_allow_html=True
        )

        st.success('Prediction Complete! The model used a K-Nearest Neighbors classifier.')

        # Display the input data in the main area for confirmation
        st.subheader('Input Data Used:')
        input_df = pd.DataFrame(input_features, columns=FEATURE_NAMES)
        st.table(input_df)