from pydantic import BaseModel

class SLAPredictRequest(BaseModel):
    support_level: str
    priority: str
    created_hour: int
    created_day: str
    assigned_team: str