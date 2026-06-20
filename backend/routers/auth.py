from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth as auth_utils

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=schemas.TokenResponse)
def login(body: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user or not auth_utils.verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = auth_utils.create_access_token(user.id)
    return schemas.TokenResponse(access_token=token, user_id=user.id, name=user.name)


@router.post("/logout")
def logout():
    return {"success": True}


@router.get("/me", response_model=schemas.UserMe)
def me(current_user: models.User = Depends(auth_utils.get_current_user)):
    return schemas.UserMe(
        user_id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        is_superuser=current_user.is_superuser,
        weekly_goal=current_user.weekly_goal,
        monthly_goal=current_user.monthly_goal,
    )
