import pandas as pd
import joblib
import os
from sklearn.linear_model import LogisticRegression
from app.db import get_db_connection
from training.feature_engineering import build_features

MODEL_NAME = "sla_model_v1"
BATCH_SIZE = 500

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")

def fetch_training_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get last trained ID
    cursor.execute("""
        SELECT last_trained_feedback_id
        FROM model_training_meta
        WHERE model_name = %s
    """, (MODEL_NAME,))
    last_id = cursor.fetchone()["last_trained_feedback_id"]

    # Fetch next batch
    cursor.execute("""
        SELECT *
        FROM sla_feedback
        WHERE id > %s
        ORDER BY id ASC
        LIMIT %s
    """, (last_id, BATCH_SIZE))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return pd.DataFrame(rows), last_id

def prepare_training_set(df):
    y = df["final_outcome"]
    X = build_features(df)
    return X, y

def train_model(X, y):
    model = LogisticRegression(
        class_weight={0: 1, 1: 20},
        max_iter=1000
    )
    model.fit(X, y)
    return model

def save_model(model, feature_columns):
    joblib.dump(
        model,
        os.path.join(MODELS_DIR, "sla_model_v1.pkl")
    )

    joblib.dump(
        list(feature_columns),
        os.path.join(MODELS_DIR, "sla_feature_columns.pkl")
    )
    
    
def update_training_meta(last_used_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE model_training_meta
        SET last_trained_feedback_id = %s
        WHERE model_name = %s
    """, (last_used_id, MODEL_NAME))

    conn.commit()
    cursor.close()
    conn.close()
    
def main():
    df, last_id = fetch_training_data()

    if len(df) < BATCH_SIZE:
        print("Not enough new data to retrain.")
        return

    X, y = prepare_training_set(df)

    model = train_model(X, y)

    save_model(model, X.columns)

    new_last_id = df["id"].max()
    update_training_meta(new_last_id)

    print("Model retrained successfully.")


if __name__ == "__main__":
    main()