from pydantic import BaseModel
class SLAFeedback(BaseModel):
    ticket_id: str
    ai_probability: float
    admin_decision: int  # 0 or 1
    final_outcome: int   # 0 or 1
    
