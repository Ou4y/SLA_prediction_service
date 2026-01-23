from fastapi import FastAPI
import pandas as pd
from app.schemas import SLAPredictRequest
from app.sla_model import predict_sla_risk, feature_columns
from app.feedback import SLAFeedback
from app.risk import risk_level
from app.explain import explain_risk
from app.db import get_db_connection
from app.rabbitmq import publish_retrain_event




app = FastAPI(title="OpsMind AI Service")

def prepare_features(request: SLAPredictRequest):
    df = pd.DataFrame([{
        "support_level": request.support_level,
        "priority": request.priority,
        "created_hour": request.created_hour,
        "created_day": request.created_day,
        "assigned_team": request.assigned_team
    }])

    # Encode categorical variables
    df_encoded = pd.get_dummies(df)

    # Ensure all expected feature columns are present
    df_encoded = df_encoded.reindex(
        columns=feature_columns,
        fill_value=0
    )

    return df_encoded
    data = {
        "support_level": [request.support_level],
        "priority": [request.priority],
        "created_hour": [request.created_hour],
        "created_day": [request.created_day],
        "assigned_team": [request.assigned_team]
    }

    df = pd.DataFrame(data)
    df_encoded = pd.get_dummies(df)

    return df_encoded

@app.post("/predict-sla")
def predict_sla(request: SLAPredictRequest):
    features = prepare_features(request)
    risk = predict_sla_risk(features)[0]

    return {
        "sla_breach_probability": float(f"{risk:.4f}")
    }
    
    
@app.post("/feedback/sla")
def log_feedback(feedback: SLAFeedback):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sla_feedback
        (ticket_id, ai_probability, admin_decision, final_outcome)
        VALUES (%s, %s, %s, %s)
    """, (
        feedback.ticket_id,
        feedback.ai_probability,
        feedback.admin_decision,
        feedback.final_outcome
    ))

    conn.commit()
    cursor.close()
    conn.close()

    # 🔑 Trigger retraining if needed
    if should_trigger_retrain("sla_model_v1"):
        publish_retrain_event("sla_model_v1")

    return {"status": "feedback saved"}
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO sla_feedback
        (ticket_id, ai_probability, admin_decision, final_outcome)
        VALUES (%s, %s, %s, %s)
    """

    cursor.execute(query, (
        feedback.ticket_id,
        feedback.ai_probability,
        feedback.admin_decision,
        feedback.final_outcome
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return {"status": "feedback saved"}

@app.post("/predict-sla-dashboard")
def predict_sla_dashboard(request: SLAPredictRequest):
    features = prepare_features(request)
    prob = predict_sla_risk(features)[0]

    return {
        "risk": risk_level(prob),
        "confidence": f"{int(prob * 100)}%",
        "reasons": explain_risk(request)
    }
    
@app.get("/")
def read_root():
    return {"status": "ok", "service": "OpsMind AI Service"}

def should_trigger_retrain(model_name: str, threshold: int = 500) -> bool:
    """
    Checks how many new feedback rows exist since last training.
    Returns True if retraining should be triggered.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM sla_feedback
        WHERE id > (
            SELECT last_trained_feedback_id
            FROM model_training_meta
            WHERE model_name = %s
        )
    """, (model_name,))

    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return count >= threshold