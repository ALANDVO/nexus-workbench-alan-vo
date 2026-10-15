from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.api.deps import get_current_active_user, get_optional_user
from app.core.auth import oidc_client
from app.core.config import get_settings
from app.core.database import get_db_session
from app.models.user import User, UserRole
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])


class AuthStartResponse(BaseModel):
    authorization_url: str
    state: str
    nonce: str
    code_verifier: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserInfo(BaseModel):
    id: int
    sub: str
    email: str | None
    username: str
    role: UserRole


@router.get("/login", response_model=AuthStartResponse)
async def login_start(request: Request):
    state = oidc_client.generate_state()
    nonce = oidc_client.generate_nonce()
    code_verifier = oidc_client.generate_code_verifier()

    request.session["oauth_state"] = state
    request.session["oauth_nonce"] = nonce
    request.session["oauth_code_verifier"] = code_verifier

    auth_url = oidc_client.build_authorization_url(state, nonce, code_verifier)
    return AuthStartResponse(
        authorization_url=auth_url, state=state, nonce=nonce, code_verifier=code_verifier
    )


@router.get("/callback")
async def login_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    db: AsyncSession = Depends(get_db_session),
):
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error: {error} - {error_description}",
        )

    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing code or state",
        )

    stored_state = request.session.get("oauth_state")
    stored_nonce = request.session.get("oauth_nonce")
    stored_code_verifier = request.session.get("oauth_code_verifier")

    if not stored_state or state != stored_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
        )

    try:
        token_data = await oidc_client.exchange_code(code, stored_code_verifier)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token exchange failed: {e}",
        )

    id_token = token_data.get("id_token")
    access_token = token_data.get("access_token")

    try:
        validated = await oidc_client.validate_token(id_token, nonce=stored_nonce)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {e}",
        )

    result = await db.execute(select(User).where(User.sub == validated.sub))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            sub=validated.sub,
            email=validated.email,
            username=validated.email or validated.sub,
            role=UserRole.VIEWER,
        )
        db.add(user)
    else:
        user.last_login = validated.iat
        if validated.email:
            user.email = validated.email

    await db.commit()
    await db.refresh(user)

    request.session.clear()

    redirect_url = f"{settings.oidc_logout_redirect_uri}?token={access_token}"
    return RedirectResponse(url=redirect_url)


@router.post("/logout")
async def logout(request: Request, current_user: User = Depends(get_current_active_user)):
    request.session.clear()
    logout_url = oidc_client.build_logout_url()
    return {"logout_url": logout_url}


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    return UserInfo(
        id=current_user.id,
        sub=current_user.sub,
        email=current_user.email,
        username=current_user.username,
        role=current_user.role,
    )


@router.get("/config")
async def get_auth_config(optional_user: User | None = Depends(get_optional_user)):
    return {
        "keycloak_url": settings.keycloak_url,
        "realm": settings.keycloak_realm,
        "client_id": settings.keycloak_client_id,
        "redirect_uri": settings.oidc_redirect_uri,
        "authenticated": optional_user is not None,
        "user": (
            {"id": optional_user.id, "username": optional_user.username, "role": optional_user.role.value}
            if optional_user
            else None
        ),
    }