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
    Function,
    VTable,
    SwitchStatement,
    CallSite,
    StringRef,
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
                        "functions": [
                            {
                                "offset": offset,
                                "name": func_name,
                            }
                            for offset, func_name in v.functions
                        ],
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

        # Rebuild AnalysisResult from stored JSON
        # Functions
        for f_data in data.get("functions", []):
            result_obj.functions.append(
                Function(
                    name=f_data["name"],
                    address=f_data["address"],
                    signature=f_data["signature"],
                    body="",
                    calls=[],
                    strings=[],
                )
            )

        # VTables
        for v_data in data.get("vtables", []):
            vfuncs = v_data.get('functions', [])
            parsed_funcs = [
                (f['offset'], f['name']) for f in vfuncs
            ] if vfuncs else []
            result_obj.vtables.append(
                VTable(
                    name=v_data['name'],
                    address=v_data['address'],
                    functions=parsed_funcs,
                )
            )

        # Switch statements
        for s_data in data.get("switches", []):
            switch = SwitchStatement(
                address=s_data["address"],
                variable=s_data["variable"],
                cases=[],
                default_target=s_data.get("default_target") if s_data.get("has_default") else None,
                default_name=None,
            )
            result_obj.switches.append(switch)

        # JMP calls
        for c_data in data.get("jmp_calls", []):
            result_obj.jmp_calls.append(
                CallSite(
                    address=0,
                    caller=c_data["caller"],
                    target=c_data["target"],
                    target_address=c_data["target_address"],
                    call_type="unknown",
                    confidence=c_data["confidence"],
                    raw_text="",
                )
            )

        # Strings
        for s_data in data.get("strings", []):
            result_obj.strings.append(
                StringRef(
                    address=s_data["address"],
                    value=s_data["value"],
                    segment=s_data["segment"],
                    references=[],
                )
            )

        # Cross-references (directly from JSON)
        if "cross_references" in data:
            result_obj.cross_references = data["cross_references"]
        return result_obj


def create_analysis_service(engine: Optional[DecompilerEngine] = None) -> AnalysisService:
    """Factory function to create an AnalysisService instance."""
    return AnalysisService(engine)
