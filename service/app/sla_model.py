import os
import joblib
import pandas as pd

# --------------------------------------------------
# Resolve BASE directory: service/app → service
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# BASE_DIR == /ai-service/service

# --------------------------------------------------
# Absolute paths to model artifacts
# --------------------------------------------------
MODEL_PATH = os.path.join(BASE_DIR, "models", "sla_model_v1.pkl")
FEATURES_PATH = os.path.join(BASE_DIR, "models", "sla_feature_columns.pkl")

# --------------------------------------------------
# Load artifacts ONCE at startup
# --------------------------------------------------
model = joblib.load(MODEL_PATH)
feature_columns = joblib.load(FEATURES_PATH)

# --------------------------------------------------
# Prediction function
# --------------------------------------------------
def predict_sla_risk(features_df: pd.DataFrame):
    return model.predict_proba(features_df)[:, 1]