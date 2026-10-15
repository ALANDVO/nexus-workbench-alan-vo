import pytest
from httpx import AsyncClient

from app.models.analysis import Analysis, AnalysisStatus, AnalysisType
from app.models.user import User, UserRole


class TestAnalyses:
    @pytest.mark.asyncio
    async def test_create_analysis_requires_auth(self, client: AsyncClient):
        response = await client.post(
            "/analyses",
            json={
                "name": "Test Analysis",
                "analysis_type": "vtable_resolution",
                "input_data": "{}",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_analyses_requires_auth(self, client: AsyncClient):
        response = await client.get("/analyses")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_analysis_as_operator(self, auth_client: AsyncClient, test_user: User):
        response = await auth_client.post(
            "/analyses",
            json={
                "name": "Test VTable Analysis",
                "analysis_type": "vtable_resolution",
                "input_data": '{"binary": "test.bin"}',
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test VTable Analysis"
        assert data["analysis_type"] == "vtable_resolution"
        assert data["status"] == "pending"
        assert data["user_id"] == test_user.id

    @pytest.mark.asyncio
    async def test_list_analyses_pagination(self, auth_client: AsyncClient, test_user: User, db_session):
        for i in range(5):
            analysis = Analysis(
                user_id=test_user.id,
                name=f"Analysis {i}",
                analysis_type=AnalysisType.VTABLE_RESOLUTION,
                status=AnalysisStatus.PENDING,
            )
            db_session.add(analysis)
        await db_session.commit()

        response = await auth_client.get("/analyses?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["items"]) == 2
        assert data["total_pages"] == 3

    @pytest.mark.asyncio
    async def test_get_analysis_by_id(self, auth_client: AsyncClient, test_user: User, db_session):
        analysis = Analysis(
            user_id=test_user.id,
            name="Specific Analysis",
            analysis_type=AnalysisType.SWITCH_RECOVERY,
            status=AnalysisStatus.COMPLETED,
            result_data='{"cases": 5}',
        )
        db_session.add(analysis)
        await db_session.commit()
        await db_session.refresh(analysis)

        response = await auth_client.get(f"/analyses/{analysis.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == analysis.id
        assert data["name"] == "Specific Analysis"
        assert data["result_data"] == '{"cases": 5}'

    @pytest.mark.asyncio
    async def test_get_analysis_not_found(self, auth_client: AsyncClient):
        response = await auth_client.get("/analyses/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_analysis_status(self, auth_client: AsyncClient, test_user: User, db_session):
        analysis = Analysis(
            user_id=test_user.id,
            name="Updatable Analysis",
            analysis_type=AnalysisType.JMP_CALL_RECOVERY,
            status=AnalysisStatus.PENDING,
        )
        db_session.add(analysis)
        await db_session.commit()
        await db_session.refresh(analysis)

        response = await auth_client.patch(
            f"/analyses/{analysis.id}",
            json={"status": "running"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["started_at"] is not None

    @pytest.mark.asyncio
    async def test_delete_analysis(self, auth_client: AsyncClient, test_user: User, db_session):
        analysis = Analysis(
            user_id=test_user.id,
            name="Deletable Analysis",
            analysis_type=AnalysisType.STRING_RECOVERY,
            status=AnalysisStatus.PENDING,
        )
        db_session.add(analysis)
        await db_session.commit()
        await db_session.refresh(analysis)

        response = await auth_client.delete(f"/analyses/{analysis.id}")
        assert response.status_code == 204

        response = await auth_client.get(f"/analyses/{analysis.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_viewer_cannot_create_analysis(self, viewer_client: AsyncClient):
        response = await viewer_client.post(
            "/analyses",
            json={"name": "Test", "analysis_type": "vtable_resolution"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_analysis_filtering(self, auth_client: AsyncClient, test_user: User, db_session):
        for status in [AnalysisStatus.PENDING, AnalysisStatus.RUNNING, AnalysisStatus.COMPLETED]:
            analysis = Analysis(
                user_id=test_user.id,
                name=f"Analysis {status.value}",
                analysis_type=AnalysisType.VTABLE_RESOLUTION,
                status=status,
            )
            db_session.add(analysis)
        await db_session.commit()

        response = await auth_client.get("/analyses?status=completed")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "completed"