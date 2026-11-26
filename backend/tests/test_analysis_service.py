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



    @pytest.mark.asyncio
    async def test_get_analysis_result(self, service: AnalysisService, db_session: AsyncSession, test_user: User):
        analysis = Analysis(
            user_id=test_user.id,
            name='Test Get Result',
            analysis_type=AnalysisType.VTABLE_RESOLUTION,
            input_data="""MyClass_vtable[] = {
                &MyClass::func1,
                &MyClass::func2,
            };
            void bar() {
                (*this->vtable[1])(local_20);
            }""",
            status=AnalysisStatus.PENDING,
        )
        db_session.add(analysis)
        await db_session.commit()
        await db_session.refresh(analysis)

        # Run the analysis to generate result_data
        result = await service.run_analysis(db_session, analysis)
        
        # Now retrieve it via get_analysis_result
        retrieved = await service.get_analysis_result(db_session, analysis.id)
        assert retrieved is not None
        # Should have at least one function from the analysis (bar)
        assert len(retrieved.functions) >= 1
        # The function names should include bar
        func_names = {f.name for f in retrieved.functions}
        assert 'bar' in func_names
        # VTables should be present and contain the vtable functions
        assert len(retrieved.vtables) >= 1
        # VTable name
        vtable_names = {v.name for v in retrieved.vtables}
        assert 'MyClass_vtable' in vtable_names
        # VTable should contain func1 and func2 (stored as (offset, name) tuples)
        vtable_func_names = {f[1] for f in retrieved.vtables[0].functions}
        assert 'MyClass::func1' in vtable_func_names
        assert 'MyClass::func2' in vtable_func_names
        # Cross references dict may be present
        assert isinstance(retrieved.cross_references, dict)