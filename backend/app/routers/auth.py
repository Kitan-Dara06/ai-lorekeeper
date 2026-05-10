import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import AuthResponse
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/session", response_model=AuthResponse)
async def exchange_session(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPBearer = Depends(HTTPBearer()),
):
    """Exchange a Supabase access token for user info.
    Frontend sends the Supabase JWT; backend validates it, ensures a local
    user record exists, and returns the user info."""
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = uuid.UUID(payload["sub"])
    email = payload.get("email", "")

    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(id=user_id, email=email)
        db.add(user)
        await db.flush()

    return AuthResponse(token=token, user_id=str(user.id), email=user.email)


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete the user and all associated data."""
    await db.delete(current_user)
    await db.flush()
    return None
