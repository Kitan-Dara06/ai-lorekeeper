import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import AuthResponse
from app.services.auth import get_or_create_user_from_token, verify_supabase_token
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/session", response_model=AuthResponse)
async def exchange_session(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPBearer = Depends(HTTPBearer()),
):
    """Exchange a Supabase access token for user info."""
    token = credentials.credentials
    payload = await verify_supabase_token(token)
    if payload is None:
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
