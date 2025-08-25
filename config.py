import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # AUTH_MODE: "AAD" | "API_KEY"
    AUTH_MODE: str = os.getenv("AUTH_MODE", "API_KEY").upper()

    # API KEY (dev mode)
    API_KEY_HEADER: str = os.getenv("API_KEY_HEADER", "x-api-key")
    API_KEY_VALUE: str = os.getenv("API_KEY_VALUE", "dev-secret")

    # Azure AD (OIDC)
    AAD_TENANT_ID: str = os.getenv("AAD_TENANT_ID", "3f9e6f5d-98bf-4cd1-bbc5-e4dc985c0a77")      # e.g. 3f9e6f5d-...
    AAD_AUDIENCE: str = os.getenv("AAD_AUDIENCE", "38a25199-49ed-4d7b-8346-41ec11a9fa6f")        # your App Registration's Application (client) ID or an exposed API 'api://...'
    AAD_ISSUER: str = os.getenv("AAD_ISSUER", "")            # optional override
    AAD_OPENID_CONFIG: str | None = None

    def __post_init__(self):
        pass

@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.AUTH_MODE == "AAD":
        # Build issuer & OIDC metadata URL if not provided
        tenant = s.AAD_TENANT_ID
        s.AAD_ISSUER = s.AAD_ISSUER or f"https://login.microsoftonline.com/{tenant}/v2.0"
        s.AAD_OPENID_CONFIG = f"https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration"
    return s
