"""Analysis service for running decompiler analyses."""

import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Analysis, AnalysisStatus, AnalysisType
from app.services.decompiler_engine import (
    AnalysisResult,
    DecompilerEngine,
    create_decompiler_engine,
)


class AnalysisService:
    """Service for executing decompiler analyses."""

    def __init__(self, engine: Optional[DecompilerEngine] = None):
        self.engine = engine or create_decompiler_engine()

    async def run_analysis(
        self,
        db: AsyncSession,
        analysis: Analysis,
    ) -> AnalysisResult:
        """Run the analysis based on its type."""
        analysis.status = AnalysisStatus.RUNNING
        analysis.started_at = datetime.now(timezone.utc)
        await db.commit()

        try:
            result = self.engine.analyze(analysis.input_data or "")
            
            # Store structured result as JSON
            result_data = {
                "functions_count": len(result.functions),
                "vtables_count": len(result.vtables),
                "switches_count": len(result.switches),
                "jmp_calls_count": len(result.jmp_calls),
                "strings_count": len(result.strings),
                "cross_references_count": len(result.cross_references),
                "functions": [
                    {
                        "name": f.name,
                        "address": f.address,
                        "signature": f.signature,
                        "calls_count": len(f.calls),
                        "strings_count": len(f.strings),
                    }
                    for f in result.functions
                ],
                "vtables": [
                    {
                        "name": v.name,
                        "address": v.address,
                        "functions_count": len(v.functions),
                    }
                    for v in result.vtables
                ],
                "switches": [
                    {
                        "address": s.address,
                        "variable": s.variable,
                        "cases_count": len(s.cases),
                        "has_default": s.default_target is not None,
                    }
                    for s in result.switches
                ],
                "jmp_calls": [
                    {
                        "caller": c.caller,
                        "target": c.target,
                        "target_address": c.target_address,
                        "confidence": c.confidence,
                    }
                    for c in result.jmp_calls
                ],
                "strings": [
                    {
                        "address": s.address,
                        "value": s.value[:100],  # Truncate long strings
                        "segment": s.segment,
                    }
                    for s in result.strings
                ],
            }
            
            analysis.result_data = json.dumps(result_data)
            analysis.status = AnalysisStatus.COMPLETED
            analysis.completed_at = datetime.now(timezone.utc)
            analysis.error_message = None
            
        except Exception as e:
            analysis.status = AnalysisStatus.FAILED
            analysis.completed_at = datetime.now(timezone.utc)
            analysis.error_message = str(e)
            raise
        
        await db.commit()
        await db.refresh(analysis)
        
        return result

    async def get_analysis_result(
        self,
        db: AsyncSession,
        analysis_id: int,
    ) -> Optional[AnalysisResult]:
        """Retrieve and parse stored analysis result."""
        result = await db.execute(select(Analysis).where(Analysis.id == analysis_id))
        analysis = result.scalar_one_or_none()
        
        if not analysis or not analysis.result_data:
            return None
        
        data = json.loads(analysis.result_data)
        result_obj = AnalysisResult()
        return result_obj


def create_analysis_service(engine: Optional[DecompilerEngine] = None) -> AnalysisService:
    """Factory function to create an AnalysisService instance."""
    return AnalysisService(engine)
