from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import verify_password, create_access_token, get_password_hash
from app.models import User
from app.schemas import Token, LoginRequest, ChangePasswordRequest

router = APIRouter(prefix="/auth", tags=["auth"])


def _authenticate(db: Session, username: str, password: str) -> User:
    """Username is the primary login identifier. Email is kept only for
    optional notifications and is never used as a login identifier."""
    user = db.query(User).filter(User.username == username.strip().lower()).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    return user


@router.post("/login", response_model=Token)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = _authenticate(db, data.username, data.password)
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return Token(access_token=token, role=user.role.value, full_name=user.full_name)


@router.post("/token", response_model=Token, include_in_schema=False)
def token_login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = _authenticate(db, form.username, form.password)
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return Token(access_token=token, role=user.role.value, full_name=user.full_name)


@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    return {"detail": "Password updated"}