from typing import Optional
from fastapi import APIRouter, Cookie, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.features.auth.models import User
from app.features.auth.dependencies import get_current_user
from app.features.auth.schemas import (
    LoginRequest,
    TokenResponse,
    UserProfileResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.features.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_async_db),
):
    service = AuthService(db)
    user = await service.authenticate_user(data)
    return await service.generate_token_pair(user, response)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_async_db),
):
    if not refresh_token:
        from app.core.exceptions import AuthenticationError
        raise AuthenticationError("Missing refresh token cookie")
    service = AuthService(db)
    return await service.refresh_tokens(refresh_token, response)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_async_db),
):
    service = AuthService(db)
    await service.logout(refresh_token, response)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserProfileResponse)
async def get_current_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = AuthService(db)
    return await service.get_user_profile(str(user.id))


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_async_db),
):
    service = AuthService(db)
    msg = await service.initiate_password_reset(data.email)
    return {"message": msg}


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_async_db),
):
    service = AuthService(db)
    await service.complete_password_reset(data.token, data.new_password)
    return {"message": "Password reset successful. Please log in with your new password."}
