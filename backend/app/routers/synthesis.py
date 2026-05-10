import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.lore import LoreSnapshot, LoreSnapshotList, LoreSnapshotListItem
from app.schemas.synthesis import (
    SynthesisRunInfo,
    SynthesisRunList,
    TriggerSynthesisRequest,
)
from app.services.synthesis import (
    get_lore_detail,
    get_lore_snapshots,
    get_synthesis_runs,
    trigger_synthesis,
)
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/synthesis", tags=["synthesis"])


@router.post("/trigger")
async def trigger(
    req: TriggerSynthesisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    run = await trigger_synthesis(db, current_user.id, req.file_ids)
    return {
        "run_id": str(run.id),
        "status": run.status,
        "message": "Synthesis completed"
        if run.status == "completed"
        else "Synthesis failed",
    }


@router.get("/runs", response_model=SynthesisRunList)
async def list_runs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    runs = await get_synthesis_runs(db, current_user.id)
    return SynthesisRunList(runs=runs, total=len(runs))


@router.get("/snapshots", response_model=LoreSnapshotList)
async def list_snapshots(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    snapshots = await get_lore_snapshots(db, current_user.id)
    return LoreSnapshotList(snapshots=snapshots, total=len(snapshots))


@router.get("/snapshots/{lore_id}", response_model=LoreSnapshot)
async def get_snapshot(
    lore_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    detail = await get_lore_detail(db, uuid.UUID(lore_id), current_user.id)
    if not detail:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return detail
