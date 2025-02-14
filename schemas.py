from pydantic import BaseModel
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


# ✅ Схема для регистрации пользователя
class UserCreate(BaseModel):
    username: str
    password: str


# ✅ Схема для входа в систему
class UserLogin(BaseModel):
    username: str
    password: str


# ✅ Схема ответа для пользователя
class UserResponse(BaseModel):
    id: int
    username: str


# ✅ Схема ответа для JWT-токена
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
