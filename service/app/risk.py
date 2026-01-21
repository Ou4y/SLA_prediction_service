def risk_level(probability: float) -> str:
    if probability >= 0.7:
        return "High"
    elif probability >= 0.4:
        return "Medium"
    return "Low"