from pydantic import BaseModel, ConfigDict
from datetime import datetime


class AlertBase(BaseModel):
    type: str
    description: str


class AlertCreate(AlertBase):
    """📌 Используется при создании тревоги (POST /alerts/)"""

    pass


class AlertResponse(AlertBase):
    """📌 Используется для ответа API (GET /alerts/, GET /alerts/{id})"""

    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
