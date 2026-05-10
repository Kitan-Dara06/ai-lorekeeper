import logging
import uuid

from jose import ExpiredSignatureError, JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)


def verify_supabase_token(token: str) -> dict | None:
    """Verify a Supabase JWT and return its payload."""
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False},
        )
        logger.info(f"Token valid for user: {payload.get('sub')}")
        return payload
    except ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        return None
    except Exception as e:
        logger.warning(f"Token verification error: {e}")
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
