# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from database import get_db
# from models import User
# from schemas import UserCreate, UserLogin, UserResponse, TokenResponse
# from services.auth import hash_password, verify_password, create_jwt_token

# router = APIRouter(prefix="/users", tags=["Users"])

# @router.post("/register", response_model=UserResponse)
# def register_user(user: UserCreate, db: Session = Depends(get_db)):
#     """Регистрирует нового пользователя"""
#     existing_user = db.query(User).filter(User.username == user.username).first()
#     if existing_user:
#         raise HTTPException(status_code=400, detail="Username already exists")

#     new_user = User(username=user.u
