import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse, Response
from starlette.requests import Request
from streamator import JobEmitter

from app.auth.deps import AuthenticatedUser, require_admin
from app.db.connection import connect
from app.netxp_members.export_ops import (
    export_content_disposition_csv,
    export_content_disposition_xlsx,
    export_rows_to_xlsx_bytes,
    fetch_netxp_members_export_rows,
    prepare_export_rows,
    write_csv_response_body,
)
from app.netxp_members.feature_config import netxp_members_settings
from app.netxp_members.models import NetxpSyncStartResponse
from app.netxp_members.query import (
    fetch_netxp_members_page,
    merge_sort_query,
    normalize_search,
    normalize_sort_dir,
)
from app.netxp_members.sync import run_sync as netxp_run_sync


router = APIRouter()

_NM = netxp_members_settings()
_LIST_DEFAULT_PAGE_SIZE = int(_NM["list_default_page_size"])
_LIST_MAX_PAGE_SIZE = int(_NM["list_max_page_size"])


# Return JSONResponse so FastAPI never runs Pydantic response validation on this dict (avoids any
# accidental inference of list[NetxpMemberOut] or stale response_field from older deployments).
@router.get("/netxp-members", tags=["admin", "netxp-members"], response_model=None)
async def list_netxp_members(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(_LIST_DEFAULT_PAGE_SIZE, ge=1, le=_LIST_MAX_PAGE_SIZE),
    search: str | None = Query(None),
    active_only: bool = Query(True),
    current_members_only: bool = Query(
        False,
        description=(
            "If true, only rows with no Austrittsdatum or Austrittsdatum strictly after today "
            "(still a member by exit date)."
        ),
    ),
    youth_only: bool = Query(
        False,
        description=(
            "If true, only members who were at most 18 years old on January 1 of the current year "
            "(known birth date)."
        ),
    ),
    csv_status_aktiv: bool = Query(
        False,
        description="Restrict to rows where NetXP CSV Status (csv_status) is aktiv.",
    ),
    csv_status_passiv: bool = Query(
        False,
        description="Restrict to rows where NetXP CSV Status (csv_status) is passiv.",
    ),
    sort_by: str | None = Query(
        None,
        description=(
            "Sort column (DB field or alias: age→geburtsdatum, member_years→eintrittsdatum, active→is_active). "
            "Omit for default name order."
        ),
    ),
    sort_dir: str = Query("asc", description="asc or desc."),
    _: AuthenticatedUser = Depends(require_admin),
) -> JSONResponse:
    search_norm = normalize_search(search)
    sort_by_q, sort_dir_q = merge_sort_query(request, sort_by=sort_by, sort_dir=sort_dir)
    sort_by_norm = sort_by_q
    sort_dir_norm = normalize_sort_dir(sort_dir_q)

    items, total = await fetch_netxp_members_page(
        page=page,
        page_size=page_size,
        search_norm=search_norm,
        active_only=active_only,
        current_members_only=current_members_only,
        youth_only=youth_only,
        csv_status_aktiv=csv_status_aktiv,
        csv_status_passiv=csv_status_passiv,
        sort_by_norm=sort_by_norm,
        sort_dir_norm=sort_dir_norm,
    )

    return JSONResponse(
        content={
            "page": page,
            "page_size": page_size,
            "total": total,
            "items": items,
            "sort_by": sort_by_norm,
            "sort_dir": sort_dir_norm if sort_by_norm else None,
        }
    )


@router.get("/netxp-members/export/xlsx", tags=["admin", "netxp-members"])
async def export_netxp_members_xlsx(
    request: Request,
    search: str | None = Query(None),
    active_only: bool = Query(True),
    current_members_only: bool = Query(False),
    youth_only: bool = Query(
        False,
        description=(
            "If true, only members who were at most 18 years old on January 1 of the current year "
            "(known birth date)."
        ),
    ),
    csv_status_aktiv: bool = Query(False),
    csv_status_passiv: bool = Query(False),
    columns: list[str] | None = Query(
        None,
        description="Repeat: limit export to these table column ids (same as column picker). Omit for all columns.",
    ),
    sort_by: str | None = Query(None),
    sort_dir: str = Query("asc"),
    _: AuthenticatedUser = Depends(require_admin),
) -> Response:
    """Excel export for current filter/sort scope (cap at export_row_limit rows from config)."""
    search_norm = normalize_search(search)
    sort_by_q, sort_dir_q = merge_sort_query(request, sort_by=sort_by, sort_dir=sort_dir)
    sort_by_norm = sort_by_q
    sort_dir_norm = normalize_sort_dir(sort_dir_q)
    row_dicts = await fetch_netxp_members_export_rows(
        search_norm=search_norm,
        active_only=active_only,
        current_members_only=current_members_only,
        youth_only=youth_only,
        csv_status_aktiv=csv_status_aktiv,
        csv_status_passiv=csv_status_passiv,
        sort_by_norm=sort_by_norm,
        sort_dir_norm=sort_dir_norm,
    )
    rows_out, fieldnames = prepare_export_rows(row_dicts, columns)
    body = export_rows_to_xlsx_bytes(rows_out, fieldnames)
    return Response(
        content=body,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": export_content_disposition_xlsx()},
    )


@router.get("/netxp-members/export", tags=["admin", "netxp-members"])
async def export_netxp_members_csv(
    request: Request,
    search: str | None = Query(None),
    active_only: bool = Query(True),
    current_members_only: bool = Query(False),
    youth_only: bool = Query(
        False,
        description=(
            "If true, only members who were at most 18 years old on January 1 of the current year "
            "(known birth date)."
        ),
    ),
    csv_status_aktiv: bool = Query(False),
    csv_status_passiv: bool = Query(False),
    columns: list[str] | None = Query(
        None,
        description="Repeat: limit export to these table column ids (same as column picker). Omit for all columns.",
    ),
    sort_by: str | None = Query(None),
    sort_dir: str = Query("asc"),
    _: AuthenticatedUser = Depends(require_admin),
) -> Response:
    """CSV export for current filter/sort scope (cap at export_row_limit rows from config)."""
    search_norm = normalize_search(search)
    sort_by_q, sort_dir_q = merge_sort_query(request, sort_by=sort_by, sort_dir=sort_dir)
    sort_by_norm = sort_by_q
    sort_dir_norm = normalize_sort_dir(sort_dir_q)
    row_dicts = await fetch_netxp_members_export_rows(
        search_norm=search_norm,
        active_only=active_only,
        current_members_only=current_members_only,
        youth_only=youth_only,
        csv_status_aktiv=csv_status_aktiv,
        csv_status_passiv=csv_status_passiv,
        sort_by_norm=sort_by_norm,
        sort_dir_norm=sort_dir_norm,
    )
    rows_out, fieldnames = prepare_export_rows(row_dicts, columns)
    body = write_csv_response_body(rows_out, fieldnames)
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": export_content_disposition_csv()},
    )


@router.post("/netxp-members/sync", tags=["admin", "netxp-members"])
async def netxp_sync_members(_: AuthenticatedUser = Depends(require_admin)) -> NetxpSyncStartResponse:
    """
    Trigger NetXP Verein members sync in write-mode (DB upsert + inactivate missing).
    """
    conn = await connect()
    try:
        running = await conn.fetchval(
            """
            SELECT 1
            FROM netxp_sync_runs
            WHERE status = 'running' AND finished_at IS NULL
            ORDER BY started_at DESC
            LIMIT 1
            """
        )
        if running:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="NetXP sync already running")
    finally:
        await conn.close()

    emitter = JobEmitter()

    async def _run() -> None:
        async with emitter:
            await netxp_run_sync(dry_run=False, limit=None, emit_event=emitter.emit)

    task = asyncio.create_task(_run())
    emitter.track(task)

    return NetxpSyncStartResponse(job_id=str(emitter.job_id))
