from typing import Any, Dict, Optional
from fastapi import Depends, Header, HTTPException, status, Request
from jose import jwt
import requests
from cachetools import TTLCache
from config import get_settings

# Simple in-memory caches for OIDC metadata and JWKS
_oidc_cache = TTLCache(maxsize=1, ttl=60 * 60)   # 1 hour
_jwks_cache = TTLCache(maxsize=1, ttl=60 * 60)

def _get_oidc() -> Dict[str, Any]:
    settings = get_settings()
    if settings.AAD_OPENID_CONFIG in _oidc_cache:
        return _oidc_cache[settings.AAD_OPENID_CONFIG]
    try:
        resp = requests.get(settings.AAD_OPENID_CONFIG, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        _oidc_cache[settings.AAD_OPENID_CONFIG] = data
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OIDC metadata fetch failed: {e}")

def _get_jwks(jwks_uri: str) -> Dict[str, Any]:
    if jwks_uri in _jwks_cache:
        return _jwks_cache[jwks_uri]
    try:
        resp = requests.get(jwks_uri, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        _jwks_cache[jwks_uri] = data
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JWKS fetch failed: {e}")

def _decode_aad_token(token: str) -> Dict[str, Any]:
    settings = get_settings()
    oidc = _get_oidc()
    jwks_uri = oidc["jwks_uri"]
    jwks = _get_jwks(jwks_uri)

    # jose expects a key resolver; we’ll pick the right key by 'kid'
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")
    key = None
    for k in jwks["keys"]:
        if k.get("kid") == kid:
            key = k
            break
    if not key:
        raise HTTPException(status_code=401, detail="Signing key not found")

    # Validate token
    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=[key.get("alg", "RS256"), "RS256", "RS384", "RS512"],
            audience=settings.AAD_AUDIENCE,
            issuer=settings.AAD_ISSUER,
            options={"verify_at_hash": False},  # typical for access tokens
        )
        return claims
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

def _auth_aad(authorization: Optional[str]) -> Dict[str, Any]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    return _decode_aad_token(token)

def _auth_api_key(provided_key: Optional[str]) -> Dict[str, Any]:
    settings = get_settings()
    if not provided_key or provided_key != settings.API_KEY_VALUE:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    # return a pseudo user/principal
    return {"sub": "api-key-user", "auth": "api_key"}

# --------- FastAPI dependencies & Strawberry context ---------

async def auth_dependency(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    api_key: Optional[str] = Header(default=None, alias=None),
):
    """
    Enforces auth according to AUTH_MODE and returns 'principal' dict.
    """
    settings = get_settings()

    if settings.AUTH_MODE == "AAD":
        principal = _auth_aad(authorization)
    elif settings.AUTH_MODE == "API_KEY":
        # Read the configured header name (default: x-api-key)
        header_name = settings.API_KEY_HEADER
        # Get header in a case-insensitive way:
        provided = request.headers.get(header_name)
        principal = _auth_api_key(provided)
    else:
        raise HTTPException(status_code=500, detail="Unsupported AUTH_MODE")

    return principal

async def graphql_context_getter(request: Request, principal=Depends(auth_dependency)):
    """
    Injects the authenticated principal into Strawberry context.
    """
    return {"request": request, "user": principal}
