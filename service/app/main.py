from fastapi import FastAPI
import pandas as pd
from app.schemas import SLAPredictRequest
from app.sla_model import predict_sla_risk, feature_columns
from app.feedback import SLAFeedback
from app.risk import risk_level
from app.explain import explain_risk

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

    # 🔑 THIS IS THE MOST IMPORTANT LINE
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
    with open("sla_feedback_log.csv", "a") as f:
        f.write(
            f"{feedback.ticket_id},"
            f"{feedback.ai_probability},"
            f"{feedback.admin_decision},"
            f"{feedback.final_outcome}\n"
        )

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