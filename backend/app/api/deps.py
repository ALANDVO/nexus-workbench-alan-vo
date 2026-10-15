from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth import TokenData, oidc_client
from app.core.config import get_settings
from app.core.database import get_db_session
from app.models.user import User, UserRole
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

settings = get_settings()
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token_data = await oidc_client.validate_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.sub == token_data.sub))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            sub=token_data.sub,
            email=token_data.email,
            username=token_data.email or token_data.sub,
            role=UserRole.VIEWER,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif user.last_login is None or user.email != token_data.email:
        user.last_login = token_data.iat
        user.email = token_data.email or user.email
        await db.commit()

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user


def require_role(*allowed_roles: UserRole):
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker


async def get_optional_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Optional[User]:
    if not credentials:
        return None

    try:
        token_data = await oidc_client.validate_token(credentials.credentials)
    except ValueError:
        return None

    result = await db.execute(select(User).where(User.sub == token_data.sub))
    return result.scalar_one_or_none()