# ruff: noqa: B008
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import (
    OrganizationContext,
    require_organization_context,
)
from app.database.models.career import ATSBoard
from app.database.session import SessionLocal
from app.services.ats_refresh import refresh_board

router = APIRouter(
    prefix="/v1/career/coverage",
    tags=["Career ATS ingestion"],
)


@router.post("/boards/{board_id}/refresh")
def refresh_registered_board(
    board_id: uuid.UUID,
    context: OrganizationContext = Depends(require_organization_context),
) -> dict[str, Any]:
    del context

    with SessionLocal() as database:
        board = database.get(ATSBoard, board_id)

        if board is None:
            raise HTTPException(
                status_code=404,
                detail="ATS board was not found.",
            )

        result = refresh_board(database, board)
        database.commit()

        return {
            "board_id": str(board.id),
            "provider": board.provider,
            "state": result.board_state,
            "successful": result.successful,
            "posting_count": result.posting_count,
            "persisted_postings": (result.persisted_postings),
            "created_canonical_jobs": (result.created_canonical_jobs),
            "deactivated_postings": (result.deactivated_postings),
            "schema_hash": result.schema_hash,
            "schema_changed": result.schema_changed,
            "adapter_version": result.adapter_version,
            "error_code": result.error_code,
            "error_message": result.error_message,
        }
