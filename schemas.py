from pydantic import BaseModel
from datetime import datetime


class AlertCreate(BaseModel):
    type: str
    description: str


class AlertResponse(AlertCreate):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True
