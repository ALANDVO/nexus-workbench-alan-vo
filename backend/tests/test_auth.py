import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from app.main import create_app
from app.models.user import User, UserRole
from app.core.auth import oidc_client
from app.core.database import get_db_session
from app.api.deps import get_current_active_user


class TestAuth:
    @pytest.mark.asyncio
    async def test_login_start_returns_url(self, client: AsyncClient):
        response = await client.get("/auth/login")
        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "state" in data
        assert "nonce" in data
        assert "code_verifier" in data
        assert data["authorization_url"].startswith("http")

    @pytest.mark.asyncio
    async def test_auth_config_unauthenticated(self, client: AsyncClient):
        response = await client.get("/auth/config")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False
        assert data["user"] is None
        assert "keycloak_url" in data
        assert "realm" in data
        assert "client_id" in data

    @pytest.mark.asyncio
    async def test_me_unauthenticated(self, client: AsyncClient):
        response = await client.get("/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_callback_missing_params(self, client: AsyncClient):
        response = await client.get("/auth/callback")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_callback_error(self, client: AsyncClient):
        response = await client.get("/auth/callback?error=access_denied&error_description=User%20denied")
        assert response.status_code == 400
        data = response.json()
        assert "OAuth error" in data["detail"]

    @pytest.mark.asyncio
    async def test_logout_requires_auth(self, client: AsyncClient):
        response = await client.post("/auth/logout")
        assert response.status_code == 401


class TestAuthWithMockedOIDC:
    @pytest.mark.asyncio
    async def test_login_flow_with_mocked_oidc(self, db_session):
        from app.core.auth import TokenData

        with patch.object(oidc_client, "discover", new_callable=AsyncMock) as mock_discover, \
             patch.object(oidc_client, "get_jwks", new_callable=AsyncMock) as mock_jwks, \
             patch.object(oidc_client, "exchange_code", new_callable=AsyncMock) as mock_exchange, \
             patch.object(oidc_client, "validate_token", new_callable=AsyncMock) as mock_validate:

            mock_discover.return_value = type("Config", (), {
                "issuer": "http://localhost:8080/realms/nexus",
                "authorization_endpoint": "http://localhost:8080/realms/nexus/protocol/openid-connect/auth",
                "token_endpoint": "http://localhost:8080/realms/nexus/protocol/openid-connect/token",
                "jwks_uri": "http://localhost:8080/realms/nexus/protocol/openid-connect/certs",
                "logout_endpoint": "http://localhost:8080/realms/nexus/protocol/openid-connect/logout",
            })()

            mock_jwks.return_value = {"keys": []}

            mock_exchange.return_value = {
                "access_token": "test-access-token",
                "id_token": "test-id-token",
                "token_type": "Bearer",
                "expires_in": 300,
            }

            mock_validate.return_value = TokenData(
                sub="test-sub-oidc",
                email="oidc@example.com",
                roles=["operator"],
                exp=9999999999,
                iat=1234567890,
            )

            app = create_app()
            app.dependency_overrides[get_db_session] = lambda: db_session

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", follow_redirects=True) as ac:
                login_resp = await ac.get("/auth/login")
                assert login_resp.status_code == 200
                login_data = login_resp.json()
                state = login_data["state"]
                nonce = login_data["nonce"]
                code_verifier = login_data["code_verifier"]

                cookie = login_resp.headers.get("set-cookie", "")

                callback_resp = await ac.get(
                    f"/auth/callback?code=test-code&state={state}",
                    headers={"cookie": cookie} if cookie else {},
                )
                assert callback_resp.status_code in (200, 302, 307)