"""Tests for the analysis service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Analysis, AnalysisStatus, AnalysisType
from app.models.user import User, UserRole
from app.services.analysis_service import AnalysisService, create_analysis_service
from app.services.decompiler_engine import create_decompiler_engine


class TestAnalysisService:
    @pytest.fixture
    def engine(self):
        return create_decompiler_engine()

    @pytest.fixture
    def service(self, engine):
        return create_analysis_service(engine)

    @pytest.mark.asyncio
    async def test_run_analysis_vtable_resolution(self, service: AnalysisService, db_session: AsyncSession, test_user: User):
        analysis = Analysis(
            user_id=test_user.id,
            name="Test VTable",
            analysis_type=AnalysisType.VTABLE_RESOLUTION,
            input_data="""
            MyClass_vtable[] = {
                &MyClass::func1,
                &MyClass::func2,
            };
            void bar() {
                (*this->vtable[1])(local_20);
            }
            """,
            status=AnalysisStatus.PENDING,
        )
        db_session.add(analysis)
        await db_session.commit()
        await db_session.refresh(analysis)

        result = await service.run_analysis(db_session, analysis)

        assert analysis.status == AnalysisStatus.COMPLETED
        assert analysis.result_data is not None
        assert len(result.functions) >= 1

    @pytest.mark.asyncio
    async def test_run_analysis_switch_recovery(self, service: AnalysisService, db_session: AsyncSession, test_user: User):
        analysis = Analysis(
            user_id=test_user.id,
            name="Test Switch",
            analysis_type=AnalysisType.SWITCH_RECOVERY,
            input_data="""
            void func() {
                if (x == 1) { goto case1; }
                if (x == 2) { goto case2; }
                if (x == 3) { goto case3; }
            }
            """,
            status=AnalysisStatus.PENDING,
        )
        db_session.add(analysis)
        await db_session.commit()
        await db_session.refresh(analysis)

        result = await service.run_analysis(db_session, analysis)

        assert analysis.status == AnalysisStatus.COMPLETED
        assert analysis.result_data is not None
        assert len(result.switches) >= 1

    @pytest.mark.asyncio
    async def test_run_analysis_empty_input(self, service: AnalysisService, db_session: AsyncSession, test_user: User):
        analysis = Analysis(
            user_id=test_user.id,
            name="Test Empty",
            analysis_type=AnalysisType.VTABLE_RESOLUTION,
            input_data=None,
            status=AnalysisStatus.PENDING,
        )
        db_session.add(analysis)
        await db_session.commit()
        await db_session.refresh(analysis)

        result = await service.run_analysis(db_session, analysis)
        assert analysis.status == AnalysisStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
