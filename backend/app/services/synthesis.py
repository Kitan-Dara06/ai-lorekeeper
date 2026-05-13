import json
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.lore import LoreOutput
from app.models.synthesis import SynthesisRun
from app.models.vault_file import VaultFile
from app.schemas.lore import GemmaLoreOutput
from app.services.gemma import call_gemma_synthesis


def _serialize_lore_field(data) -> str:
    """Serialize a lore field to JSON string for DB storage."""
    if isinstance(data, str):
        return data
    return json.dumps(data, default=str)


def _deserialize_lore_field(data: str):
    """Deserialize a JSON string from DB back to Python object."""
    if not data:
        return []
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return data


async def trigger_synthesis(
    db: AsyncSession,
    user_id: uuid.UUID,
    file_ids: Optional[list[str]] = None,
) -> SynthesisRun:
    """Create a synthesis run, start background processing, return immediately."""
    if file_ids:
        ids = [uuid.UUID(fid) for fid in file_ids]
    else:
        result = await db.execute(
            select(VaultFile.id).where(VaultFile.user_id == user_id)
        )
        ids = [row[0] for row in result.fetchall()]

    run = SynthesisRun(
        user_id=user_id,
        file_ids=ids,
        status="running",
    )
    db.add(run)
    await db.flush()
    await db.commit()

    # Fire-and-forget: start synthesis in background
    import asyncio

    asyncio.create_task(_run_synthesis_background(run.id, user_id, ids))

    return run


async def _run_synthesis_background(
    run_id: uuid.UUID,
    user_id: uuid.UUID,
    file_ids: list[uuid.UUID],
):
    """Run synthesis in the background (separate session to avoid conflicts)."""
    from app.database import async_session_factory

    async with async_session_factory() as db:
        try:
            run = await db.get(SynthesisRun, run_id)
            if not run:
                return

            batched = await _collect_and_batch_content(db, user_id, file_ids)
            raw_output = await call_gemma_synthesis(batched)

            if raw_output is None:
                raise ValueError("Gemma returned no output")

            validated = GemmaLoreOutput(**raw_output)

            lore = LoreOutput(
                run_id=run.id,
                user_id=user_id,
                the_sentence=validated.the_sentence,
                narrative=validated.narrative,
                story_arcs=_serialize_lore_field(
                    [a.model_dump(by_alias=True) for a in validated.story_arcs]
                ),
                recurring_people=_serialize_lore_field(
                    [p.model_dump(by_alias=True) for p in validated.recurring_people]
                ),
                defining_moments=_serialize_lore_field(
                    [m.model_dump(by_alias=True) for m in validated.defining_moments]
                ),
                mindset_shifts=_serialize_lore_field(
                    [s.model_dump(by_alias=True) for s in validated.mindset_shifts]
                ),
                core_themes=_serialize_lore_field(validated.core_themes),
                identity_contradictions=_serialize_lore_field(
                    [c.model_dump() for c in validated.identity_contradictions]
                ),
            )
            db.add(lore)
            run.status = "completed"

        except Exception as e:
            run.status = "failed"
            lore = LoreOutput(
                run_id=run_id,
                user_id=user_id,
                the_sentence="Synthesis failed on this run.",
                narrative=f"An error occurred: {str(e)}",
                story_arcs="[]",
                recurring_people="[]",
                defining_moments="[]",
                mindset_shifts="[]",
                core_themes="[]",
                identity_contradictions="[]",
            )
            db.add(lore)

        await db.commit()


async def _collect_and_batch_content(
    db: AsyncSession,
    user_id: uuid.UUID,
    file_ids: list[uuid.UUID],
) -> str:
    """Collect all file content sorted chronologically by period_start."""
    if not file_ids:
        return "No files selected for synthesis."

    result = await db.execute(
        select(VaultFile)
        .where(VaultFile.id.in_(file_ids))
        .where(VaultFile.user_id == user_id)
        .order_by(VaultFile.period_start.nulls_last(), VaultFile.uploaded_at)
    )
    files = result.scalars().all()

    batches = []
    total_chars = 0
    for f in files:
        period_info = ""
        if f.period_start:
            period_info = f"[Period: {f.period_start.strftime('%Y-%m')}"
            if f.period_end:
                period_info += f" to {f.period_end.strftime('%Y-%m')}"
            period_info += "]"

        tag_info = f"[Source: {f.source_tag}]" if f.source_tag else ""
        header = f"\n--- FILE: {f.filename} {tag_info} {period_info} ---\n"
        content = f.extracted_text or "[No extractable text]"

        entry = f"{header}{content}\n"

        if total_chars + len(entry) > settings.MAX_TEXT_CHARS_PER_BATCH:
            break

        batches.append(entry)
        total_chars += len(entry)

    return "\n".join(batches) if batches else "No content available for synthesis."


async def get_lore_snapshots(db: AsyncSession, user_id: uuid.UUID) -> list[dict]:
    """Get all lore snapshots for a user, newest first."""
    result = await db.execute(
        select(LoreOutput, SynthesisRun)
        .join(SynthesisRun, LoreOutput.run_id == SynthesisRun.id)
        .where(LoreOutput.user_id == user_id)
        .order_by(LoreOutput.created_at.desc())
    )
    rows = result.fetchall()

    snapshots = []
    for lore, run in rows:
        snapshots.append(
            {
                "id": str(lore.id),
                "run_id": str(run.id),
                "the_sentence": lore.the_sentence,
                "created_at": lore.created_at.isoformat(),
                "status": run.status,
            }
        )
    return snapshots


async def get_lore_detail(
    db: AsyncSession, lore_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[dict]:
    """Get full detail for a specific lore snapshot."""
    result = await db.execute(
        select(LoreOutput, SynthesisRun)
        .join(SynthesisRun, LoreOutput.run_id == SynthesisRun.id)
        .where(LoreOutput.id == lore_id)
        .where(LoreOutput.user_id == user_id)
    )
    row = result.fetchone()
    if not row:
        return None

    lore, run = row
    return {
        "id": str(lore.id),
        "run_id": str(run.id),
        "the_sentence": lore.the_sentence,
        "narrative": lore.narrative,
        "story_arcs": _deserialize_lore_field(lore.story_arcs),
        "recurring_people": _deserialize_lore_field(lore.recurring_people),
        "defining_moments": _deserialize_lore_field(lore.defining_moments),
        "mindset_shifts": _deserialize_lore_field(lore.mindset_shifts),
        "core_themes": _deserialize_lore_field(lore.core_themes),
        "identity_contradictions": _deserialize_lore_field(
            lore.identity_contradictions
        ),
        "created_at": lore.created_at.isoformat(),
        "run_triggered_at": run.triggered_at.isoformat(),
        "file_count": len(run.file_ids),
    }


async def get_synthesis_runs(db: AsyncSession, user_id: uuid.UUID) -> list[dict]:
    """Get all synthesis runs for a user."""
    result = await db.execute(
        select(SynthesisRun)
        .where(SynthesisRun.user_id == user_id)
        .order_by(SynthesisRun.triggered_at.desc())
    )
    runs = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "file_count": len(r.file_ids),
            "triggered_at": r.triggered_at.isoformat(),
            "status": r.status,
        }
        for r in runs
    ]
