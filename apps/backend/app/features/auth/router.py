from typing import List, Optional
from fastapi import APIRouter, Cookie, Depends, Request, Response, status
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
    ChangePasswordRequest,
    SessionResponse,
)
from app.features.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_db),
):
    service = AuthService(db)
    return await service.login(data, response, request)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    request: Request,
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_async_db),
):
    service = AuthService(db)
    return await service.refresh_tokens(refresh_token, response, request)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_async_db),
):
    service = AuthService(db)
    await service.logout(refresh_token, response)
    # Returns None on purpose: returning a fresh Response here would replace the
    # injected one and drop the refresh-cookie deletion header the service just
    # wrote, leaving the (now server-side revoked) cookie sitting in the browser.


@router.get("/me", response_model=UserProfileResponse)
async def get_current_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = AuthService(db)
    return service.get_current_user_profile(user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: ChangePasswordRequest,
    request: Request,
    user: User = Depends(get_current_user),
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_async_db),
):
    service = AuthService(db)
    await service.change_password(user, data, refresh_token, request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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


@router.get("/sessions", response_model=List[SessionResponse])
async def list_my_sessions(
    user: User = Depends(get_current_user),
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_async_db),
):
    service = AuthService(db)
    return await service.list_my_sessions(user, refresh_token)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_my_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = AuthService(db)
    await service.revoke_my_session(user, session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
