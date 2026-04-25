from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ....db import get_db
from ....dependencies.auth import get_current_user
from ....models.user_account import UserAccount
from ....schemas.auth import AuthResponse, LoginRequest, SignUpRequest, UserProfile
from ....security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_profile(user: UserAccount) -> UserProfile:
    return UserProfile(id=user.id, email=user.email, role=user.role)


@router.post("/signup", response_model=AuthResponse)
async def sign_up(payload: SignUpRequest, db: Session = Depends(get_db)) -> AuthResponse:
    existing = db.execute(
        select(UserAccount).where(UserAccount.email == payload.email.lower())
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    try:
        user = UserAccount(
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            role=payload.role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to create account right now.",
        ) from exc

    token = create_access_token(user_id=user.id, email=user.email, role=user.role)
    return AuthResponse(access_token=token, user=_to_profile(user))


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.execute(
        select(UserAccount).where(UserAccount.email == payload.email.lower())
    ).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(user_id=user.id, email=user.email, role=user.role)
    return AuthResponse(access_token=token, user=_to_profile(user))


@router.get("/me", response_model=UserProfile)
async def me(current_user: UserAccount = Depends(get_current_user)) -> UserProfile:
    return _to_profile(current_user)
