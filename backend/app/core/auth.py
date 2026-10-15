import secrets
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlencode

import httpx
from jose import jwt
from jose.exceptions import JWTError

from app.core.config import get_settings

settings = get_settings()


@dataclass
class TokenData:
    sub: str
    email: Optional[str]
    roles: list[str]
    exp: int
    iat: int


@dataclass
class OIDCConfig:
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str
    logout_endpoint: str


class OIDCClient:
    def __init__(self):
        self._config: Optional[OIDCConfig] = None
        self._jwks: Optional[dict] = None
        self._jwks_fetched_at: float = 0
        self._jwks_ttl = 3600

    async def discover(self) -> OIDCConfig:
        if self._config:
            return self._config

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(settings.oidc_discovery_url)
            resp.raise_for_status()
            data = resp.json()

        self._config = OIDCConfig(
            issuer=data["issuer"],
            authorization_endpoint=data["authorization_endpoint"],
            token_endpoint=data["token_endpoint"],
            jwks_uri=data["jwks_uri"],
            logout_endpoint=data.get("end_session_endpoint", settings.oidc_logout_endpoint),
        )
        return self._config

    async def get_jwks(self) -> dict:
        now = time.time()
        if self._jwks and (now - self._jwks_fetched_at) < self._jwks_ttl:
            return self._jwks

        config = await self.discover()
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(config.jwks_uri)
            resp.raise_for_status()
            self._jwks = resp.json()
            self._jwks_fetched_at = now
        return self._jwks

    def build_authorization_url(self, state: str, nonce: str, code_verifier: str) -> str:
        config = self._config or OIDCConfig(
            issuer=settings.oidc_issuer,
            authorization_endpoint=settings.oidc_authorization_endpoint,
            token_endpoint=settings.oidc_token_endpoint,
            jwks_uri=settings.oidc_jwks_uri,
            logout_endpoint=settings.oidc_logout_endpoint,
        )
        code_challenge = self._pkce_challenge(code_verifier)
        params = {
            "response_type": "code",
            "client_id": settings.keycloak_client_id,
            "redirect_uri": settings.oidc_redirect_uri,
            "scope": "openid profile email roles",
            "state": state,
            "nonce": nonce,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return f"{config.authorization_endpoint}?{urlencode(params)}"

    async def exchange_code(self, code: str, code_verifier: str) -> dict:
        config = await self.discover()
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                config.token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.oidc_redirect_uri,
                    "client_id": settings.keycloak_client_id,
                    "client_secret": settings.keycloak_client_secret,
                    "code_verifier": code_verifier,
                },
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            return resp.json()

    async def validate_token(self, token: str, nonce: Optional[str] = None) -> TokenData:
        jwks = await self.get_jwks()
        config = await self.discover()

        try:
            payload = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                audience=settings.keycloak_client_id,
                issuer=config.issuer,
                options={"verify_at_hash": False},
            )
        except JWTError as e:
            raise ValueError(f"Invalid token: {e}")

        if nonce and payload.get("nonce") != nonce:
            raise ValueError("Nonce mismatch")

        roles = payload.get("realm_access", {}).get("roles", [])
        return TokenData(
            sub=payload["sub"],
            email=payload.get("email"),
            roles=roles,
            exp=payload["exp"],
            iat=payload["iat"],
        )

    def build_logout_url(self, id_token_hint: Optional[str] = None) -> str:
        config = self._config or OIDCConfig(
            issuer=settings.oidc_issuer,
            authorization_endpoint=settings.oidc_authorization_endpoint,
            token_endpoint=settings.oidc_token_endpoint,
            jwks_uri=settings.oidc_jwks_uri,
            logout_endpoint=settings.oidc_logout_endpoint,
        )
        params = {"post_logout_redirect_uri": settings.oidc_logout_redirect_uri}
        if id_token_hint:
            params["id_token_hint"] = id_token_hint
        return f"{config.logout_endpoint}?{urlencode(params)}"

    @staticmethod
    def _pkce_challenge(verifier: str) -> str:
        import base64
        import hashlib
        digest = hashlib.sha256(verifier.encode()).digest()
        return base64.urlsafe_b64encode(digest).decode().rstrip("=")

    @staticmethod
    def generate_code_verifier() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_state() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_nonce() -> str:
        return secrets.token_urlsafe(32)


oidc_client = OIDCClient()