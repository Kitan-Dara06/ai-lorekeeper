import base64
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


async def verify_supabase_token(token: str) -> dict | None:
    """Verify a Supabase JWT using JWKS (handles ES256/RS256/HS256)."""
    parts = _decode_jwt_parts(token)
    if not parts:
        logger.warning("Malformed JWT")
        return None

    header, _payload, _sig = parts
    alg = header.get("alg", "HS256")
    kid = header.get("kid")
    logger.info(f"JWT alg={alg}, kid={kid}")

    # ES256 / RS256 — fetch public key from Supabase JWKS
    if alg in ("ES256", "RS256"):
        try:
            jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
            async with httpx.AsyncClient() as client:
                resp = await client.get(jwks_url)
                resp.raise_for_status()
                keys = resp.json().get("keys", [])

            # Find key matching kid, or use first
            key_data = None
            for k in keys:
                if kid and k.get("kid") == kid:
                    key_data = k
                    break
            if not key_data and keys:
                key_data = keys[0]

            if not key_data:
                logger.warning("No JWKS keys found")
                return None

            public_key = jwk.construct(key_data)
            payload = jwt.decode(
                token,
                public_key,
                algorithms=[alg],
                options={"verify_exp": False},
            )
            logger.info(f"Token valid: user={payload.get('sub')} alg={alg}")
            return payload

        except Exception as e:
            logger.warning(f"JWKS verify failed: {e}")
            return None

    # HS256 — use shared secret
    secret = settings.SUPABASE_JWT_SECRET
    if not secret:
        logger.warning("SUPABASE_JWT_SECRET not configured")
        return None

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_exp": False},
        )
        logger.info(f"HS256 token valid: user={payload.get('sub')}")
        return payload
    except Exception as e:
        logger.warning(f"HS256 verify failed: {e}")
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
