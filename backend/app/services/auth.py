import uuid

from jose import jwt

from app.config import settings


def verify_supabase_token(token: str) -> dict | None:
    """Verify a Supabase JWT and return its payload."""
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except Exception:
        return None


def get_or_create_user_from_token(db, payload: dict):
    """Get local user record, creating one if it doesn't exist."""
    user_id = uuid.UUID(payload["sub"])
    email = payload.get("email", "")

    from sqlalchemy import select

    from app.models.user import User

    result = db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(id=user_id, email=email)
        db.add(user)
        db.flush()

    return user
