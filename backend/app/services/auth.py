import base64
import hashlib
import hmac
import json
import logging
import uuid

import httpx
from jose import jwk, jwt

from app.config import settings

logger = logging.getLogger(__name__)


def _base64url_decode(data: str) -> bytes:
    """Decode base64url with padding."""
    rem = len(data) % 4
    if rem:
        data += "=" * (4 - rem)
    return base64.urlsafe_b64decode(data)


def _decode_jwt_parts(token: str) -> tuple[dict, dict, str] | None:
    """Split JWT into (header, payload, signature_b64)."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header = json.loads(_base64url_decode(parts[0]))
        payload = json.loads(_base64url_decode(parts[1]))
        return header, payload, parts[2]
    except Exception as e:
        logger.warning(f"Failed to parse JWT: {e}")
        return None


def _verify_hmac(token: str, secret: str) -> dict | None:
    """Verify an HS256 JWT using HMAC-SHA256."""
    parts = _decode_jwt_parts(token)
    if not parts:
        return None
    header, payload, sig_b64 = parts

    # Recreate the signing input
    message = token.rsplit(".", 1)[0]
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    # Decode the provided signature
    try:
        actual_sig = _base64url_decode(sig_b64)
    except Exception:
        logger.warning("Failed to decode signature")
        return None

    if not hmac.compare_digest(expected_sig, actual_sig):
        logger.warning("HMAC signature mismatch")
        return None

    return payload


async def verify_supabase_token(token: str) -> dict | None:
    """Verify a Supabase JWT. Tries HMAC (HS256) first, then JWKS (RS256)."""
    parts = _decode_jwt_parts(token)
    if not parts:
        logger.warning("Malformed JWT")
        return None

    header, _payload, _sig = parts
    alg = header.get("alg", "HS256")
    logger.info(f"JWT alg: {alg}, kid: {header.get('kid')}")

    if alg == "RS256":
        # RS256 — fetch public key from JWKS
        try:
            jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
            logger.info(f"Fetching JWKS from {jwks_url}")
            async with httpx.AsyncClient() as client:
                resp = await client.get(jwks_url)
                resp.raise_for_status()
                keys = resp.json().get("keys", [])

            kid = header.get("kid")
            key_data = None
            for k in keys:
                if k.get("kid") == kid or key_data is None:
                    key_data = k

            if key_data:
                public_key = jwk.construct(key_data)
                payload = jwt.decode(
                    token,
                    public_key,
                    algorithms=["RS256"],
                    options={"verify_exp": False},
                )
                logger.info(f"RS256 token valid for user: {payload.get('sub')}")
                return payload
        except Exception as e:
            logger.warning(f"RS256 verification failed: {e}")
            return None

    # HS256 — verify HMAC signature manually
    secret = settings.SUPABASE_JWT_SECRET
    if not secret:
        logger.warning("SUPABASE_JWT_SECRET not configured")
        return None

    payload = _verify_hmac(token, secret)
    if payload:
        logger.info(f"HS256 token valid for user: {payload.get('sub')}")
        return payload

    logger.warning("Token verification failed")
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
