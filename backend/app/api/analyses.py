from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, require_role
from app.core.database import get_db_session
from app.models.analysis import Analysis, AnalysisStatus, AnalysisType
from app.models.user import User, UserRole
from app.services.analysis_service import create_analysis_service
from app.services.decompiler_engine import AnalysisResult

router = APIRouter(prefix="/analyses", tags=["analyses"])

analysis_service = create_analysis_service()


class AnalysisRunResponse(BaseModel):
    analysis_id: int
    status: AnalysisStatus
    functions_count: int
    vtables_count: int
    switches_count: int
    jmp_calls_count: int
    strings_count: int
    cross_references_count: int


class AnalysisCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    analysis_type: AnalysisType
    input_data: Optional[str] = None


class AnalysisUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[AnalysisStatus] = None
    result_data: Optional[str] = None
    error_message: Optional[str] = None


class AnalysisResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    analysis_type: AnalysisType
    status: AnalysisStatus
    input_data: Optional[str]
    result_data: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    user_id: int

    class Config:
        from_attributes = True


class AnalysisListResponse(BaseModel):
    items: list[AnalysisResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    data: AnalysisCreate,
    current_user: Annotated[User, Depends(require_role(UserRole.OPERATOR, UserRole.ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    analysis = Analysis(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        analysis_type=data.analysis_type,
        input_data=data.input_data,
        status=AnalysisStatus.PENDING,
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    return analysis


@router.post("/{analysis_id}/run", response_model=AnalysisRunResponse)
async def run_analysis(
    analysis_id: int,
    current_user: Annotated[User, Depends(require_role(UserRole.OPERATOR, UserRole.ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    result = await db.execute(
        select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == current_user.id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
        )

    if analysis.status == AnalysisStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Analysis is already running",
        )

    # Run the analysis
    result_data = await analysis_service.run_analysis(db, analysis)

    return AnalysisRunResponse(
        analysis_id=analysis.id,
        status=analysis.status,
        functions_count=len(result_data.functions),
        vtables_count=len(result_data.vtables),
        switches_count=len(result_data.switches),
        jmp_calls_count=len(result_data.jmp_calls),
        strings_count=len(result_data.strings),
        cross_references_count=len(result_data.cross_references),
    )


@router.get("", response_model=AnalysisListResponse)
async def list_analyses(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[AnalysisStatus] = Query(None, alias="status"),
    analysis_type: Optional[AnalysisType] = None,
):
    query = select(Analysis).where(Analysis.user_id == current_user.id)

    if status_filter:
        query = query.where(Analysis.status == status_filter)
    if analysis_type:
        query = query.where(Analysis.analysis_type == analysis_type)

    query = query.order_by(Analysis.created_at.desc())

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    items = result.scalars().all()

    total_pages = (total + page_size - 1) // page_size

    return AnalysisListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    result = await db.execute(
        select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == current_user.id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
        )

    return analysis


@router.patch("/{analysis_id}", response_model=AnalysisResponse)
async def update_analysis(
    analysis_id: int,
    data: AnalysisUpdate,
    current_user: Annotated[User, Depends(require_role(UserRole.OPERATOR, UserRole.ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    result = await db.execute(
        select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == current_user.id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
        )

    update_data = data.model_dump(exclude_unset=True)

    if "status" in update_data:
        new_status = update_data["status"]
        if new_status == AnalysisStatus.RUNNING and analysis.status == AnalysisStatus.PENDING:
            analysis.started_at = datetime.now(timezone.utc)
        elif new_status in (AnalysisStatus.COMPLETED, AnalysisStatus.FAILED):
            analysis.completed_at = datetime.now(timezone.utc)

    for field, value in update_data.items():
        setattr(analysis, field, value)

    analysis.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(analysis)
    return analysis


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(
    analysis_id: int,
    current_user: Annotated[User, Depends(require_role(UserRole.OPERATOR, UserRole.ADMIN))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    result = await db.execute(
        select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == current_user.id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
        )

    await db.delete(analysis)
    await db.commit()
