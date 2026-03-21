"""Anonymous aggregate-only NetXP membership statistics (no PII in responses)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.db.connection import connect

router = APIRouter(tags=["public"])

_BUCKET_KEYS: tuple[str, ...] = (
    "b0_9",
    "b10_19",
    "b20_29",
    "b30_39",
    "b40_49",
    "b50_59",
    "b60_69",
    "b70_79",
    "b80_plus",
)

_METRIC_IDS: tuple[str, ...] = (
    "all_current_aktiv_or_passiv",
    "no_exit_date",
    "aktiv_no_exit",
    "leaving_this_year_still_member",
    "current_aktiv",
    "current_passiv",
)


_STATS_SQL = """
WITH m AS (
    SELECT
        geburtsdatum,
        austrittsdatum,
        is_active,
        lower(nullif(trim(csv_status), '')) AS status_norm
    FROM netxp_members
),
enriched AS (
    SELECT
        m.geburtsdatum,
        m.austrittsdatum,
        m.is_active,
        m.status_norm,
        (m.status_norm = 'aktiv') AS is_aktiv,
        (m.status_norm = 'passiv') AS is_passiv,
        (m.status_norm IN ('aktiv', 'passiv')) AS in_ap,
        (m.austrittsdatum IS NULL OR m.austrittsdatum > CURRENT_DATE) AS current_exit,
        CASE
            WHEN m.geburtsdatum IS NULL THEN NULL
            ELSE EXTRACT(
                YEAR FROM age(
                    (date_trunc('year', CURRENT_DATE)::date),
                    m.geburtsdatum
                )
            )::integer
        END AS age_y
    FROM m
),
b AS (
    SELECT
        *,
        CASE
            WHEN age_y IS NULL THEN NULL
            WHEN age_y < 10 THEN 0
            WHEN age_y < 20 THEN 1
            WHEN age_y < 30 THEN 2
            WHEN age_y < 40 THEN 3
            WHEN age_y < 50 THEN 4
            WHEN age_y < 60 THEN 5
            WHEN age_y < 70 THEN 6
            WHEN age_y < 80 THEN 7
            ELSE 8
        END AS age_bucket
    FROM enriched
),
flags AS (
    SELECT
        *,
        (
            is_active
            AND in_ap
            AND current_exit
        ) AS seg_all_current,
        (
            is_active
            AND in_ap
            AND austrittsdatum IS NULL
        ) AS seg_no_exit,
        (
            is_active
            AND is_aktiv
            AND austrittsdatum IS NULL
        ) AS seg_aktiv_no_exit,
        (
            is_active
            AND in_ap
            AND austrittsdatum IS NOT NULL
            AND austrittsdatum > CURRENT_DATE
            AND austrittsdatum
                <= (date_trunc('year', CURRENT_DATE) + interval '1 year - 1 day')::date
        ) AS seg_leaving_year,
        (
            is_active
            AND is_aktiv
            AND current_exit
        ) AS seg_aktiv,
        (
            is_active
            AND is_passiv
            AND current_exit
        ) AS seg_passiv
    FROM b
)
SELECT
    (date_trunc('year', CURRENT_DATE)::date) AS jan_1,
    EXTRACT(YEAR FROM date_trunc('year', CURRENT_DATE))::integer AS ref_year,

    COUNT(*) FILTER (WHERE seg_all_current) AS m0_total,
    COUNT(*) FILTER (WHERE seg_all_current AND age_bucket IS NULL) AS m0_unknown_age,
    COUNT(*) FILTER (WHERE seg_all_current AND age_bucket = 0) AS m0_b0,
    COUNT(*) FILTER (WHERE seg_all_current AND age_bucket = 1) AS m0_b1,
    COUNT(*) FILTER (WHERE seg_all_current AND age_bucket = 2) AS m0_b2,
    COUNT(*) FILTER (WHERE seg_all_current AND age_bucket = 3) AS m0_b3,
    COUNT(*) FILTER (WHERE seg_all_current AND age_bucket = 4) AS m0_b4,
    COUNT(*) FILTER (WHERE seg_all_current AND age_bucket = 5) AS m0_b5,
    COUNT(*) FILTER (WHERE seg_all_current AND age_bucket = 6) AS m0_b6,
    COUNT(*) FILTER (WHERE seg_all_current AND age_bucket = 7) AS m0_b7,
    COUNT(*) FILTER (WHERE seg_all_current AND age_bucket = 8) AS m0_b8,

    COUNT(*) FILTER (WHERE seg_no_exit) AS m1_total,
    COUNT(*) FILTER (WHERE seg_no_exit AND age_bucket IS NULL) AS m1_unknown_age,
    COUNT(*) FILTER (WHERE seg_no_exit AND age_bucket = 0) AS m1_b0,
    COUNT(*) FILTER (WHERE seg_no_exit AND age_bucket = 1) AS m1_b1,
    COUNT(*) FILTER (WHERE seg_no_exit AND age_bucket = 2) AS m1_b2,
    COUNT(*) FILTER (WHERE seg_no_exit AND age_bucket = 3) AS m1_b3,
    COUNT(*) FILTER (WHERE seg_no_exit AND age_bucket = 4) AS m1_b4,
    COUNT(*) FILTER (WHERE seg_no_exit AND age_bucket = 5) AS m1_b5,
    COUNT(*) FILTER (WHERE seg_no_exit AND age_bucket = 6) AS m1_b6,
    COUNT(*) FILTER (WHERE seg_no_exit AND age_bucket = 7) AS m1_b7,
    COUNT(*) FILTER (WHERE seg_no_exit AND age_bucket = 8) AS m1_b8,

    COUNT(*) FILTER (WHERE seg_aktiv_no_exit) AS m2_total,
    COUNT(*) FILTER (WHERE seg_aktiv_no_exit AND age_bucket IS NULL) AS m2_unknown_age,
    COUNT(*) FILTER (WHERE seg_aktiv_no_exit AND age_bucket = 0) AS m2_b0,
    COUNT(*) FILTER (WHERE seg_aktiv_no_exit AND age_bucket = 1) AS m2_b1,
    COUNT(*) FILTER (WHERE seg_aktiv_no_exit AND age_bucket = 2) AS m2_b2,
    COUNT(*) FILTER (WHERE seg_aktiv_no_exit AND age_bucket = 3) AS m2_b3,
    COUNT(*) FILTER (WHERE seg_aktiv_no_exit AND age_bucket = 4) AS m2_b4,
    COUNT(*) FILTER (WHERE seg_aktiv_no_exit AND age_bucket = 5) AS m2_b5,
    COUNT(*) FILTER (WHERE seg_aktiv_no_exit AND age_bucket = 6) AS m2_b6,
    COUNT(*) FILTER (WHERE seg_aktiv_no_exit AND age_bucket = 7) AS m2_b7,
    COUNT(*) FILTER (WHERE seg_aktiv_no_exit AND age_bucket = 8) AS m2_b8,

    COUNT(*) FILTER (WHERE seg_leaving_year) AS m3_total,
    COUNT(*) FILTER (WHERE seg_leaving_year AND age_bucket IS NULL) AS m3_unknown_age,
    COUNT(*) FILTER (WHERE seg_leaving_year AND age_bucket = 0) AS m3_b0,
    COUNT(*) FILTER (WHERE seg_leaving_year AND age_bucket = 1) AS m3_b1,
    COUNT(*) FILTER (WHERE seg_leaving_year AND age_bucket = 2) AS m3_b2,
    COUNT(*) FILTER (WHERE seg_leaving_year AND age_bucket = 3) AS m3_b3,
    COUNT(*) FILTER (WHERE seg_leaving_year AND age_bucket = 4) AS m3_b4,
    COUNT(*) FILTER (WHERE seg_leaving_year AND age_bucket = 5) AS m3_b5,
    COUNT(*) FILTER (WHERE seg_leaving_year AND age_bucket = 6) AS m3_b6,
    COUNT(*) FILTER (WHERE seg_leaving_year AND age_bucket = 7) AS m3_b7,
    COUNT(*) FILTER (WHERE seg_leaving_year AND age_bucket = 8) AS m3_b8,

    COUNT(*) FILTER (WHERE seg_aktiv) AS m4_total,
    COUNT(*) FILTER (WHERE seg_aktiv AND age_bucket IS NULL) AS m4_unknown_age,
    COUNT(*) FILTER (WHERE seg_aktiv AND age_bucket = 0) AS m4_b0,
    COUNT(*) FILTER (WHERE seg_aktiv AND age_bucket = 1) AS m4_b1,
    COUNT(*) FILTER (WHERE seg_aktiv AND age_bucket = 2) AS m4_b2,
    COUNT(*) FILTER (WHERE seg_aktiv AND age_bucket = 3) AS m4_b3,
    COUNT(*) FILTER (WHERE seg_aktiv AND age_bucket = 4) AS m4_b4,
    COUNT(*) FILTER (WHERE seg_aktiv AND age_bucket = 5) AS m4_b5,
    COUNT(*) FILTER (WHERE seg_aktiv AND age_bucket = 6) AS m4_b6,
    COUNT(*) FILTER (WHERE seg_aktiv AND age_bucket = 7) AS m4_b7,
    COUNT(*) FILTER (WHERE seg_aktiv AND age_bucket = 8) AS m4_b8,

    COUNT(*) FILTER (WHERE seg_passiv) AS m5_total,
    COUNT(*) FILTER (WHERE seg_passiv AND age_bucket IS NULL) AS m5_unknown_age,
    COUNT(*) FILTER (WHERE seg_passiv AND age_bucket = 0) AS m5_b0,
    COUNT(*) FILTER (WHERE seg_passiv AND age_bucket = 1) AS m5_b1,
    COUNT(*) FILTER (WHERE seg_passiv AND age_bucket = 2) AS m5_b2,
    COUNT(*) FILTER (WHERE seg_passiv AND age_bucket = 3) AS m5_b3,
    COUNT(*) FILTER (WHERE seg_passiv AND age_bucket = 4) AS m5_b4,
    COUNT(*) FILTER (WHERE seg_passiv AND age_bucket = 5) AS m5_b5,
    COUNT(*) FILTER (WHERE seg_passiv AND age_bucket = 6) AS m5_b6,
    COUNT(*) FILTER (WHERE seg_passiv AND age_bucket = 7) AS m5_b7,
    COUNT(*) FILTER (WHERE seg_passiv AND age_bucket = 8) AS m5_b8
FROM flags
"""


def _row_to_payload(row: object) -> dict[str, object]:
    r = dict(row)
    jan_1: date = r["jan_1"]
    ref_year: int = int(r["ref_year"])

    metrics: dict[str, object] = {}
    for mi, mid in enumerate(_METRIC_IDS):
        prefix = f"m{mi}_"
        buckets = [int(r[f"{prefix}b{i}"] or 0) for i in range(9)]
        metrics[mid] = {
            "total": int(r[f"{prefix}total"] or 0),
            "unknown_age": int(r[f"{prefix}unknown_age"] or 0),
            "buckets": buckets,
        }

    return {
        "reference_year": ref_year,
        "age_as_of": jan_1.isoformat(),
        "bucket_keys": list(_BUCKET_KEYS),
        "metrics": metrics,
    }


@router.get("/public/netxp-member-stats", response_model=None)
async def netxp_member_public_stats() -> JSONResponse:
    """Aggregate membership counts by age bucket; no authentication; no personal data."""
    conn = await connect()
    try:
        row = await conn.fetchrow(_STATS_SQL)
        if row is None:
            payload = {
                "reference_year": date.today().year,
                "age_as_of": f"{date.today().year}-01-01",
                "bucket_keys": list(_BUCKET_KEYS),
                "metrics": {
                    mid: {"total": 0, "unknown_age": 0, "buckets": [0] * 9}
                    for mid in _METRIC_IDS
                },
            }
            return JSONResponse(
                content=payload,
                headers={"Cache-Control": "no-store, max-age=0"},
            )
        return JSONResponse(
            content=_row_to_payload(row),
            headers={"Cache-Control": "no-store, max-age=0"},
        )
    finally:
        await conn.close()
