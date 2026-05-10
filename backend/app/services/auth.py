import base64
import json
import logging
import uuid

import httpx
from jose import jwk, jwt

from app.config import settings

logger = logging.getLogger(__name__)

# Cache the JWKS client so we don't fetch on every request
_jwks_client = None


def _get_jwks_client():
    """Get or create the JWKS client for verifying Supabase tokens."""
    global _jwks_client
    if _jwks_client is None:
        jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        _jwks_client = JWKSClient(jwks_url)
    return _jwks_client


class JWKSClient:
    """Fetches and caches Supabase JWKS for RS256 token verification."""

    def __init__(self, url: str):
        self.url = url
        self.keys = None

    async def get_public_key(self, token: str) -> str | None:
        if not self.keys:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(self.url)
                    resp.raise_for_status()
                    self.keys = resp.json().get("keys", [])
            except Exception as e:
                logger.warning(f"Failed to fetch JWKS: {e}")
                return None

        # Get the key ID from the token header
        header = self._decode_header(token)
        if not header:
            return None

        kid = header.get("kid")
        for key in self.keys:
            if key.get("kid") == kid:
                return jwk.construct(key)

        # Fallback: use first key if no kid match
        if self.keys:
            return jwk.construct(self.keys[0])
        return None

    @staticmethod
    def _decode_header(token: str) -> dict | None:
        try:
            header_b64 = token.split(".")[0]
            padding = 4 - len(header_b64) % 4
            if padding != 4:
                header_b64 += "=" * padding
            return json.loads(base64.urlsafe_b64decode(header_b64))
        except Exception:
            return None


async def verify_supabase_token(token: str) -> dict | None:
    """Verify a Supabase JWT and return its payload. Handles both RS256 and HS256."""
    # Decode header to check algorithm
    header = JWKSClient._decode_header(token)
    if header:
        logger.info(f"JWT alg: {header.get('alg')}, kid: {header.get('kid')}")

    alg = (header or {}).get("alg", "HS256")

    try:
        if alg == "RS256":
            # RS256 — use JWKS public key
            public_key = await _get_jwks_client().get_public_key(token)
            if public_key is None:
                logger.warning("Could not get public key from JWKS")
                return None
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"verify_exp": False},
            )
        else:
            # HS256 — use shared secret (or fallback)
            secret = settings.SUPABASE_JWT_SECRET
            if not secret:
                logger.warning("SUPABASE_JWT_SECRET not configured")
                return None
            payload = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                options={"verify_exp": False},
            )

        logger.info(f"Token valid for user: {payload.get('sub')}")
        return payload

    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
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
