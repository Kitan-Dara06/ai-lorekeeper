import base64
import json
import logging
import uuid

from jose import ExpiredSignatureError, JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)


def _decode_jwt_header(token: str) -> dict | None:
    """Decode just the JWT header without verifying."""
    try:
        header_b64 = token.split(".")[0]
        padding = 4 - len(header_b64) % 4
        if padding != 4:
            header_b64 += "=" * padding
        return json.loads(base64.urlsafe_b64decode(header_b64))
    except Exception:
        return None


def verify_supabase_token(token: str) -> dict | None:
    """Verify a Supabase JWT and return its payload."""
    # Log the algorithm from the token header
    header = _decode_jwt_header(token)
    if header:
        logger.info(
            f"JWT header algorithm: {header.get('alg')}, type: {header.get('typ')}"
        )

    # Try without specifying algorithms (let jose detect from header)
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            options={"verify_exp": False},
        )
        logger.info(f"Token valid for user: {payload.get('sub')}")
        return payload
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None
    except Exception as e:
        logger.warning(f"Unexpected error: {e}")
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
