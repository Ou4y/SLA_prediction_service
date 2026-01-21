import pandas as pd

def build_features(df: pd.DataFrame):
    """
    Converts raw feedback rows into model-ready features
    """
    X = df[[
        "support_level",
        "priority",
        "created_hour",
        "created_day",
        "assigned_team"
    ]]

    X_encoded = pd.get_dummies(X)

    return X_encoded