import os
import shutil
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.vault_file import VaultFile
from app.schemas.vault_file import FileListItem, FileListResponse, FileUploadResponse
from app.services.file_processor import (
    ALLOWED_TYPES,
    MAX_SIZE_BYTES,
    extract_text,
    get_file_type,
    infer_period_from_filename,
)
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post(
    "/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED
)
async def upload_file(
    file: UploadFile = File(...),
    source_tag: str = Form(None),
    period_start: str = Form(None),
    period_end: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate file type
    file_type = get_file_type(file.filename)
    if file_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file_type}' not supported. Allowed: {', '.join(sorted(ALLOWED_TYPES))}",
        )

    # Read content and check size
    content = await file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # Save to disk
    user_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)

    file_id = uuid.uuid4()
    safe_filename = f"{file_id}_{file.filename}"
    storage_path = os.path.join(user_dir, safe_filename)

    with open(storage_path, "wb") as f:
        f.write(content)

    # Extract text
    extracted = extract_text(storage_path, file_type)

    # Parse period metadata
    ps = None
    pe = None
    if period_start:
        try:
            ps = datetime.fromisoformat(period_start)
        except ValueError:
            pass
    if period_end:
        try:
            pe = datetime.fromisoformat(period_end)
        except ValueError:
            pass

    # Infer from filename if not provided
    if ps is None and pe is None:
        inferred_ps, inferred_pe = infer_period_from_filename(file.filename)
        ps = ps or inferred_ps
        pe = pe or inferred_pe

    # Create DB record
    vault_file = VaultFile(
        id=file_id,
        user_id=current_user.id,
        filename=file.filename,
        file_type=file_type,
        source_tag=source_tag,
        period_start=ps,
        period_end=pe,
        storage_path=storage_path,
        extracted_text=extracted,
    )
    db.add(vault_file)
    await db.flush()

    return FileUploadResponse(
        id=str(vault_file.id),
        filename=vault_file.filename,
        file_type=vault_file.file_type,
        source_tag=vault_file.source_tag,
        period_start=vault_file.period_start.isoformat()
        if vault_file.period_start
        else None,
        period_end=vault_file.period_end.isoformat() if vault_file.period_end else None,
        uploaded_at=vault_file.uploaded_at.isoformat(),
    )


@router.get("/", response_model=FileListResponse)
async def list_files(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VaultFile)
        .where(VaultFile.user_id == current_user.id)
        .order_by(VaultFile.uploaded_at.desc())
    )
    files = result.scalars().all()

    items = [
        FileListItem(
            id=str(f.id),
            filename=f.filename,
            file_type=f.file_type,
            source_tag=f.source_tag,
            period_start=f.period_start.isoformat() if f.period_start else None,
            period_end=f.period_end.isoformat() if f.period_end else None,
            uploaded_at=f.uploaded_at.isoformat(),
            has_extracted_text=bool(f.extracted_text),
        )
        for f in files
    ]

    return FileListResponse(files=items, total=len(items))


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VaultFile).where(
            VaultFile.id == uuid.UUID(file_id),
            VaultFile.user_id == current_user.id,
        )
    )
    vault_file = result.scalar_one_or_none()
    if not vault_file:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete from disk
    if os.path.exists(vault_file.storage_path):
        os.remove(vault_file.storage_path)

    # Delete from DB
    await db.delete(vault_file)
    await db.flush()
    return None
