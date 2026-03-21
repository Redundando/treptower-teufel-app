from __future__ import annotations

import argparse
import asyncio
import base64
import csv
import hashlib
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable, TypedDict

from app.config import CONFIG
from app.db.connection import connect


TYPED_FIELDS_BY_HEADER: dict[str, str] = {
    # CSV header -> our typed column
    "Mitgliedsnummer": "mitgliedsnummer",
    "Vorname": "vorname",
    "Nachname": "nachname",
    "Geburtsdatum": "geburtsdatum",
    "Eintrittsdatum": "eintrittsdatum",
    "Austrittsdatum": "austrittsdatum",
    "Mitgliedsart": "mitgliedsart",
    "Straße": "strasse",
    "PLZ": "plz",
    "Ort": "ort",
    "Telefon_Arbeit": "telefon_arbeit",
    "Telefon_Privat": "telefon_privat",
    "EMail_Privat": "email_privat",
    "NxSspRegistrationCode": "nx_ssp_registration_code",
    "Beitragsnamen": "beitragsnamen",
    "Info": "info",
    "Status": "csv_status",
}


def _maybe_emit_event(
    emit_event: Callable[[dict[str, Any]], None] | None,
    payload: dict[str, Any],
) -> None:
    if not emit_event:
        return
    try:
        emit_event(payload)
    except Exception:
        # Never fail the sync because an optional streaming callback misbehaves.
        return


DATE_GERMAN_RE = re.compile(r"^(?P<dd>\d{2})\.(?P<mm>\d{2})\.(?P<yyyy>\d{4})$")


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None

    # NetXP CSV often exports like "21.06.1997 00:00:00" (date + time).
    date_token = value.split(None, 1)[0]

    m = DATE_GERMAN_RE.match(date_token)
    if m:
        dd = int(m.group("dd"))
        mm = int(m.group("mm"))
        yyyy = int(m.group("yyyy"))
        try:
            return date(yyyy, mm, dd)
        except ValueError:
            return None

    # ISO date, optionally with time (fromisoformat accepts extended forms in 3.11+)
    try:
        return date.fromisoformat(value)
    except ValueError:
        pass
    try:
        return date.fromisoformat(date_token)
    except ValueError:
        return None


def parse_optional_int(value: str | None) -> int | None:
    if not value:
        return None
    s = value.strip()
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def parse_netxp_auth(auth: str) -> tuple[str, str]:
    """
    Expected format:
      NETXP_CLUB_ID#NETXP_USERNAME:NETXP_PASSWORD
    """
    auth = (auth or "").strip()
    if ":" not in auth:
        raise ValueError("NETXP_AUTH must be in the form NETXP_CLUB_ID#NETXP_USERNAME:NETXP_PASSWORD")

    auth_user, auth_password = auth.rsplit(":", 1)
    if not auth_user or not auth_password:
        raise ValueError("NETXP_AUTH missing username or password part")
    return auth_user, auth_password


class NetxpSyncConfig(TypedDict):
    members_csv_url: str
    auth_user: str
    auth_password: str
    timeout_seconds: int


def load_netxp_sync_config() -> NetxpSyncConfig:
    cfg = CONFIG["features"]["netxp_sync_members"]

    members_csv_url = (os.getenv("NETXP_MEMBERS_CSV_URL") or str(cfg["members_csv_url"])).strip()
    netxp_auth = os.getenv("NETXP_AUTH", "").strip()
    club_id = (os.getenv("NETXP_CLUB_ID") or str(cfg["club_id"])).strip()
    netxp_username = (os.getenv("NETXP_USERNAME") or str(cfg["username"])).strip()
    netxp_password = os.getenv("NETXP_PASSWORD", "").strip()
    timeout_seconds_env = os.getenv("NETXP_TIMEOUT_SECONDS", "").strip()
    timeout_seconds_default = int(cfg["timeout_seconds_default"])
    timeout_seconds = int(timeout_seconds_env or str(timeout_seconds_default))

    if not members_csv_url:
        raise RuntimeError("NETXP_MEMBERS_CSV_URL not set")

    # Support two env formats:
    # 1) NETXP_AUTH=NETXP_CLUB_ID#NETXP_USERNAME:NETXP_PASSWORD
    # 2) NETXP_CLUB_ID / NETXP_USERNAME / NETXP_PASSWORD as separate variables.
    if not netxp_auth:
        if not (club_id and netxp_username and netxp_password):
            raise RuntimeError(
                "NetXP auth not configured. Set either NETXP_AUTH "
                "or all of NETXP_CLUB_ID, NETXP_USERNAME, NETXP_PASSWORD."
            )
        netxp_auth = f"{club_id}#{netxp_username}:{netxp_password}"

    auth_user, auth_password = parse_netxp_auth(netxp_auth)
    return {
        "members_csv_url": members_csv_url,
        "auth_user": auth_user,
        "auth_password": auth_password,
        "timeout_seconds": timeout_seconds,
    }


def basic_auth_header(username: str, password: str) -> str:
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def _download_csv_sync(
    *,
    url: str,
    auth_user: str,
    auth_password: str,
    timeout_seconds: int,
    dest_path: Path,
) -> tuple[int, str]:
    """
    Download CSV to dest_path, returning (bytes_downloaded, sha256_hex).

    Auth strategy:
    - Try Basic with Authorization header.
    - If we get a 401 and a Digest challenge, retry with DigestAuthHandler.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    auth_header = basic_auth_header(auth_user, auth_password)

    def _download_with_request(request: urllib.request.Request) -> tuple[int, str]:
        sha = hashlib.sha256()
        total = 0
        with urllib.request.urlopen(request, timeout=timeout_seconds) as resp, open(dest_path, "wb") as f:
            # Defensive: ensure content-type is CSV-ish (optional; don't fail hard).
            for chunk in iter(lambda: resp.read(1024 * 128), b""):
                f.write(chunk)
                total += len(chunk)
                sha.update(chunk)
        return total, sha.hexdigest()

    req_basic = urllib.request.Request(url, headers={"Authorization": auth_header, "User-Agent": "tttc-api-netxp-sync"})
    try:
        return _download_with_request(req_basic)
    except urllib.error.HTTPError as e:
        if e.code != 401:
            raise

        www_auth = e.headers.get("WWW-Authenticate", "") if e.headers else ""
        wants_digest = "digest" in www_auth.lower()
        if not wants_digest:
            raise

        # Retry with Digest
        password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        # Use realm=None to allow matching whatever realm NetXP provides.
        password_mgr.add_password(None, url, auth_user, auth_password)
        digest_handler = urllib.request.HTTPDigestAuthHandler(password_mgr)
        opener = urllib.request.build_opener(digest_handler)

        sha = hashlib.sha256()
        total = 0
        # Important: avoid sending the Basic header on digest retry.
        req_digest = urllib.request.Request(url, headers={"User-Agent": "tttc-api-netxp-sync"})
        with opener.open(req_digest, timeout=timeout_seconds) as resp, open(dest_path, "wb") as f:
            for chunk in iter(lambda: resp.read(1024 * 128), b""):
                f.write(chunk)
                total += len(chunk)
                sha.update(chunk)

        return total, sha.hexdigest()


def _pick_encoding(sample_bytes: bytes) -> str:
    # Try UTF-8 first (with strict errors). If that fails, fall back to common legacy encodings.
    candidates = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
    for enc in candidates:
        try:
            sample_bytes.decode(enc, errors="strict")
            return enc
        except UnicodeDecodeError:
            continue
    return "latin-1"


@dataclass(frozen=True)
class ParsedNetxpRow:
    netxp_id: str
    typed: dict[str, Any]  # maps typed column -> value
    raw: dict[str, str]  # all headers -> string value
    raw_hash: str


MEMBERS_COLUMNS: list[str] = [
    "mitgliedsnummer",
    "vorname",
    "nachname",
    "geburtsdatum",
    "eintrittsdatum",
    "austrittsdatum",
    "mitgliedsart",
    "strasse",
    "plz",
    "ort",
    "telefon_privat",
    "telefon_arbeit",
    "email_privat",
    "nx_ssp_registration_code",
    "beitragsnamen",
    "info",
    "csv_status",
]


@dataclass(frozen=True)
class SyncCounts:
    inserted: int
    updated: int
    unchanged: int
    inactivated: int


def compute_diff_counts(
    *,
    parsed_rows: list[ParsedNetxpRow],
    existing_by_id: dict[str, Any],
) -> tuple[int, int, int]:
    inserted = 0
    updated = 0
    unchanged = 0
    for pr in parsed_rows:
        ex = existing_by_id.get(pr.netxp_id)
        if ex is None:
            inserted += 1
            continue

        same_hash = ex["netxp_raw_hash"] == pr.raw_hash
        if same_hash and ex["is_active"]:
            unchanged += 1
        else:
            updated += 1

    return inserted, updated, unchanged


async def fetch_existing_members(conn, *, netxp_ids: list[str]) -> dict[str, Any]:
    if not netxp_ids:
        return {}
    rows = await conn.fetch(
        "SELECT netxp_id, netxp_raw_hash, is_active FROM netxp_members WHERE netxp_id = ANY($1::text[])",
        netxp_ids,
    )
    return {r["netxp_id"]: r for r in rows}


async def count_inactivated_members(conn, *, netxp_ids: list[str]) -> int:
    if not netxp_ids:
        return await conn.fetchval("SELECT COUNT(*) FROM netxp_members WHERE is_active=true")
    return await conn.fetchval(
        """
        SELECT COUNT(*)
        FROM netxp_members
        WHERE is_active = true
          AND netxp_id <> ALL($1::text[])
        """,
        netxp_ids,
    )


def build_members_upsert_query(members_columns: list[str]) -> str:
    typed_start = 2
    typed_end_exclusive = typed_start + len(members_columns)
    raw_param = typed_end_exclusive
    raw_hash_param = typed_end_exclusive + 1
    typed_placeholders = ", ".join(f"${i}" for i in range(typed_start, typed_end_exclusive))

    return f"""
    INSERT INTO netxp_members (
      netxp_id,
      is_active,
      first_seen_at,
      last_seen_at,
      inactive_since,
      {", ".join(members_columns)},
      netxp_raw,
      netxp_raw_hash,
      updated_at
    )
    VALUES (
      $1,
      true,
      now(),
      now(),
      NULL,
      {typed_placeholders},
      ${raw_param},
      ${raw_hash_param},
      now()
    )
    ON CONFLICT (netxp_id) DO UPDATE SET
      {", ".join(f"{c} = EXCLUDED.{c}" for c in members_columns)},
      netxp_raw = EXCLUDED.netxp_raw,
      netxp_raw_hash = EXCLUDED.netxp_raw_hash,
      is_active = true,
      inactive_since = NULL,
      last_seen_at = now(),
      updated_at = now()
    """


def _typed_column_value_for_db(column: str, value: Any) -> Any:
    """mitgliedsnummer is BIGINT; asyncpg requires Python int, never str."""
    if column != "mitgliedsnummer":
        return value
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    s = str(value).strip()
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def build_members_upsert_values(
    *,
    parsed_rows: list[ParsedNetxpRow],
    members_columns: list[str],
) -> list[tuple[Any, ...]]:
    values: list[tuple[Any, ...]] = []
    for pr in parsed_rows:
        typed_values = [
            _typed_column_value_for_db(col, pr.typed.get(col)) for col in members_columns
        ]
        # Pass a dict; asyncpg encodes it to JSONB. (A JSON *string* param was stored/read oddly for some clients.)
        values.append(
            (
                pr.netxp_id,
                *typed_values,
                pr.raw,
                pr.raw_hash,
            )
        )
    return values


async def deactivate_missing_members(conn, *, netxp_ids: list[str]) -> int:
    # Works for empty netxp_ids as well (inactivates everyone that is currently active).
    return await conn.fetchval(
        """
        WITH upd AS (
          UPDATE netxp_members
          SET is_active = false,
              inactive_since = now(),
              updated_at = now()
          WHERE is_active = true
            AND netxp_id <> ALL($1::text[])
          RETURNING 1
        )
        SELECT COUNT(*) FROM upd
        """,
        netxp_ids,
    )


async def create_sync_run_record(
    conn,
    *,
    source_url: str,
    download_bytes: int,
    encoding_used: str,
    row_count: int,
    headers: list[str],
    file_hash: str,
) -> Any:
    return await conn.fetchval(
        """
        INSERT INTO netxp_sync_runs (
          status, source_url, download_bytes, encoding_used,
          delimiter, row_count, headers, file_hash,
          inserted_count, updated_count, unchanged_count,
          inactivated_count, error_count
        )
        VALUES (
          'running', $1, $2, $3, ';', $4, CAST($5 AS jsonb), $6,
          0, 0, 0, 0, 0
        )
        RETURNING id
        """,
        source_url,
        download_bytes,
        encoding_used,
        row_count,
        json.dumps(headers, ensure_ascii=False),
        file_hash,
    )


async def mark_sync_run_dry_run(
    conn,
    *,
    run_id: Any,
    counts: SyncCounts,
    error_count: int,
    notes: str,
) -> None:
    await conn.execute(
        """
        UPDATE netxp_sync_runs
        SET status = 'dry_run',
            finished_at = now(),
            inserted_count = $1,
            updated_count = $2,
            unchanged_count = $3,
            inactivated_count = $4,
            error_count = $5,
            notes = $6
        WHERE id = $7
        """,
        counts.inserted,
        counts.updated,
        counts.unchanged,
        counts.inactivated,
        error_count,
        notes,
        run_id,
    )


async def mark_sync_run_success(
    conn,
    *,
    run_id: Any,
    counts: SyncCounts,
    error_count: int,
) -> None:
    await conn.execute(
        """
        UPDATE netxp_sync_runs
        SET status = 'success',
            finished_at = now(),
            inserted_count = $1,
            updated_count = $2,
            unchanged_count = $3,
            inactivated_count = $4,
            error_count = $5
        WHERE id = $6
        """,
        counts.inserted,
        counts.updated,
        counts.unchanged,
        counts.inactivated,
        error_count,
        run_id,
    )


async def mark_sync_run_failed(conn, *, run_id: Any, error_message: str) -> None:
    await conn.execute(
        """
        UPDATE netxp_sync_runs
        SET status = 'failed',
            finished_at = now(),
            error_count = COALESCE(error_count, 0) + 1,
            notes = $1
        WHERE id = $2
        """,
        error_message[:2000],
        run_id,
    )


def _parse_csv_sync(
    *,
    csv_path: Path,
    encoding: str,
    limit: int | None,
) -> tuple[str, list[str], list[ParsedNetxpRow]]:
    with open(csv_path, "rb") as f:
        sample = f.read(200_000)
    detected_encoding = _pick_encoding(sample)
    # Prefer detected encoding, but still allow overriding by caller.
    encoding_to_use = encoding or detected_encoding

    with open(csv_path, "r", encoding=encoding_to_use, newline="") as f_text:
        reader = csv.reader(f_text, delimiter=";")
        headers_raw = next(reader)  # can raise if empty file
        # Strip BOM / whitespace so "Mitgliedsnummer" matches TYPED_FIELDS_BY_HEADER (BIGINT bind needs int).
        headers = [h.strip().lstrip("\ufeff") for h in headers_raw]
        header_to_index = {h: i for i, h in enumerate(headers)}

        if "ID" not in header_to_index:
            raise RuntimeError("CSV header missing required column `ID`")

        rows: list[ParsedNetxpRow] = []
        for row in reader:
            if limit is not None and len(rows) >= limit:
                break

            # Normalize row length (CSV parsers can drop trailing empty cells)
            if len(row) < len(headers):
                row = row + [""] * (len(headers) - len(row))
            elif len(row) > len(headers):
                row = row[: len(headers)]

            raw = {}
            for i, h in enumerate(headers):
                v = row[i].strip()
                raw[h] = v

            netxp_id = raw.get("ID", "").strip()
            if not netxp_id:
                continue

            typed: dict[str, Any] = {}
            for csv_header, typed_col in TYPED_FIELDS_BY_HEADER.items():
                if csv_header not in raw:
                    continue
                typed_val = raw.get(csv_header)
                if csv_header == "Mitgliedsnummer":
                    typed[typed_col] = parse_optional_int(typed_val)
                elif csv_header in {"Geburtsdatum", "Eintrittsdatum", "Austrittsdatum"}:
                    typed[typed_col] = parse_date(typed_val)
                else:
                    typed[typed_col] = typed_val or None

            # NetXP may emit the column with different casing; mirror into typed csv_status.
            if not typed.get("csv_status"):
                for alt in ("Status", "STATUS", "status"):
                    if alt not in raw:
                        continue
                    v = (raw.get(alt) or "").strip()
                    if v:
                        typed["csv_status"] = v
                        break

            # Hash the entire raw row so diffs are stable across runs.
            raw_hash = hashlib.sha256(
                json.dumps(raw, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest()

            rows.append(ParsedNetxpRow(netxp_id=netxp_id, typed=typed, raw=raw, raw_hash=raw_hash))

    return encoding_to_use, headers, rows


@dataclass(frozen=True)
class DownloadAndParseResult:
    download_bytes: int
    file_hash: str
    encoding_used: str
    headers: list[str]
    parsed_rows: list[ParsedNetxpRow]


async def download_and_parse_netxp_csv(
    *,
    members_csv_url: str,
    auth_user: str,
    auth_password: str,
    timeout_seconds: int,
    limit: int | None,
) -> DownloadAndParseResult:
    tmpdir = Path(tempfile.gettempdir())
    csv_path = tmpdir / f"tttc_netxp_members_{int(time.time())}.csv"

    download_bytes, file_hash = await asyncio.to_thread(
        _download_csv_sync,
        url=members_csv_url,
        auth_user=auth_user,
        auth_password=auth_password,
        timeout_seconds=timeout_seconds,
        dest_path=csv_path,
    )

    try:
        encoding_used, headers, parsed_rows = _parse_csv_sync(
            csv_path=csv_path, encoding="", limit=limit
        )
        return DownloadAndParseResult(
            download_bytes=download_bytes,
            file_hash=file_hash,
            encoding_used=encoding_used,
            headers=headers,
            parsed_rows=parsed_rows,
        )
    finally:
        # Keep no raw CSV long-term.
        try:
            csv_path.unlink(missing_ok=True)
        except Exception:
            pass


async def run_sync(
    *,
    dry_run: bool,
    limit: int | None,
    emit_event: Callable[[dict[str, Any]], None] | None = None,
) -> int:
    started = time.time()

    _maybe_emit_event(
        emit_event,
        {
            "event": "netxp_sync_started",
            "dry_run": dry_run,
            "limit": limit,
        },
    )

    cfg = load_netxp_sync_config()
    netxp_csv = await download_and_parse_netxp_csv(
        members_csv_url=cfg["members_csv_url"],
        auth_user=cfg["auth_user"],
        auth_password=cfg["auth_password"],
        timeout_seconds=cfg["timeout_seconds"],
        limit=limit,
    )

    _maybe_emit_event(
        emit_event,
        {
            "event": "netxp_sync_download_and_parse_done",
            "download_bytes": netxp_csv.download_bytes,
            "encoding_used": netxp_csv.encoding_used,
            "row_count": len(netxp_csv.parsed_rows),
            "file_hash": netxp_csv.file_hash,
        },
    )

    conn = await connect()
    try:
        return await sync_run_lifecycle(
            conn,
            source_url=cfg["members_csv_url"],
            download_bytes=netxp_csv.download_bytes,
            encoding_used=netxp_csv.encoding_used,
            row_count=len(netxp_csv.parsed_rows),
            headers=netxp_csv.headers,
            file_hash=netxp_csv.file_hash,
            parsed_rows=netxp_csv.parsed_rows,
            dry_run=dry_run,
            limit=limit,
            started=started,
            emit_event=emit_event,
        )
    finally:
        await conn.close()


async def sync_run_lifecycle(
    conn,
    *,
    source_url: str,
    download_bytes: int,
    encoding_used: str,
    row_count: int,
    headers: list[str],
    file_hash: str,
    parsed_rows: list[ParsedNetxpRow],
    dry_run: bool,
    limit: int | None,
    started: float,
    emit_event: Callable[[dict[str, Any]], None] | None,
) -> int:
    netxp_ids = [r.netxp_id for r in parsed_rows]
    run_id = await create_sync_run_record(
        conn,
        source_url=source_url,
        download_bytes=download_bytes,
        encoding_used=encoding_used,
        row_count=row_count,
        headers=headers,
        file_hash=file_hash,
    )

    _maybe_emit_event(
        emit_event,
        {
            "event": "netxp_sync_run_record_created",
            "run_id": str(run_id),
        },
    )
    try:
        existing_by_id = await fetch_existing_members(conn, netxp_ids=netxp_ids)
        inserted, updated, unchanged = compute_diff_counts(
            parsed_rows=parsed_rows,
            existing_by_id=existing_by_id,
        )
        error_count = 0

        _maybe_emit_event(
            emit_event,
            {
                "event": "netxp_sync_diff_counts",
                "inserted": inserted,
                "updated": updated,
                "unchanged": unchanged,
                "dry_run": dry_run,
                "inactivation_limit": limit,
            },
        )

        if dry_run:
            return await perform_dry_run(
                conn,
                run_id=run_id,
                started=started,
                parsed_rows=parsed_rows,
                netxp_ids=netxp_ids,
                inserted=inserted,
                updated=updated,
                unchanged=unchanged,
                inactivation_limit=limit,
                error_count=error_count,
                emit_event=emit_event,
            )

        return await perform_write_mode(
            conn,
            run_id=run_id,
            started=started,
            parsed_rows=parsed_rows,
            netxp_ids=netxp_ids,
            inserted=inserted,
            updated=updated,
            unchanged=unchanged,
            error_count=error_count,
            emit_event=emit_event,
        )
    except Exception as e:
        _maybe_emit_event(
            emit_event,
            {
                "event": "netxp_sync_failed",
                "error": str(e)[:2000],
            },
        )
        await mark_sync_run_failed(conn, run_id=run_id, error_message=str(e))
        raise


async def perform_dry_run(
    conn,
    *,
    run_id: Any,
    started: float,
    parsed_rows: list[ParsedNetxpRow],
    netxp_ids: list[str],
    inserted: int,
    updated: int,
    unchanged: int,
    inactivation_limit: int | None,
    error_count: int,
    emit_event: Callable[[dict[str, Any]], None] | None,
) -> int:
    if inactivation_limit is not None:
        inactivated = 0
        inactivation_note = f"Dry-run with --limit={inactivation_limit}: inactivation count disabled."
    else:
        inactivation_note = ""
        inactivated = await count_inactivated_members(conn, netxp_ids=netxp_ids)

    counts = SyncCounts(
        inserted=inserted,
        updated=updated,
        unchanged=unchanged,
        inactivated=inactivated,
    )

    notes = "Dry-run: no member rows were modified."
    if inactivation_note:
        notes = f"{notes} {inactivation_note}"

    await mark_sync_run_dry_run(
        conn,
        run_id=run_id,
        counts=counts,
        error_count=error_count,
        notes=notes,
    )

    _maybe_emit_event(
        emit_event,
        {
            "event": "netxp_sync_dry_run_done",
            "inserted": inserted,
            "updated": updated,
            "unchanged": unchanged,
            "inactivated": inactivated,
            "error_count": error_count,
        },
    )

    duration_s = time.time() - started
    print(
        f"NetXP sync dry-run complete: rows={len(parsed_rows)} inserted={inserted} updated={updated} "
        f"unchanged={unchanged} inactivated={inactivated} duration_s={duration_s:.2f}"
    )
    return 0


async def perform_write_mode(
    conn,
    *,
    run_id: Any,
    started: float,
    parsed_rows: list[ParsedNetxpRow],
    netxp_ids: list[str],
    inserted: int,
    updated: int,
    unchanged: int,
    error_count: int,
    emit_event: Callable[[dict[str, Any]], None] | None,
) -> int:
    _maybe_emit_event(
        emit_event,
        {
            "event": "netxp_sync_write_started",
            "inserted": inserted,
            "updated": updated,
            "unchanged": unchanged,
        },
    )

    # Write mode (transaction): upsert everything, then inactivate missing members.
    insert_query = build_members_upsert_query(MEMBERS_COLUMNS)
    values = build_members_upsert_values(
        parsed_rows=parsed_rows,
        members_columns=MEMBERS_COLUMNS,
    )

    async with conn.transaction():
        await conn.executemany(insert_query, values)
        inactivated_written = await deactivate_missing_members(
            conn, netxp_ids=netxp_ids
        )

    counts = SyncCounts(
        inserted=inserted,
        updated=updated,
        unchanged=unchanged,
        inactivated=inactivated_written,
    )
    await mark_sync_run_success(
        conn,
        run_id=run_id,
        counts=counts,
        error_count=error_count,
    )

    _maybe_emit_event(
        emit_event,
        {
            "event": "netxp_sync_success",
            "inserted": inserted,
            "updated": updated,
            "unchanged": unchanged,
            "inactivated": inactivated_written,
            "error_count": error_count,
        },
    )

    duration_s = time.time() - started
    print(
        f"NetXP sync complete: rows={len(parsed_rows)} inserted={inserted} updated={updated} "
        f"unchanged={unchanged} inactivated={inactivated_written} duration_s={duration_s:.2f}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync NetXP Verein members CSV into PostgreSQL.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Download + parse + diff, but do not write to DB.",
    )
    parser.add_argument(
        "--progress-events",
        action="store_true",
        help="Emit structured progress events as JSON lines to stdout.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="For testing: process only first N CSV rows. Only allowed with --dry-run.",
    )
    args = parser.parse_args(argv)

    if args.limit is not None and not args.dry_run:
        print("--limit is only supported together with --dry-run", file=sys.stderr)
        return 2

    emit_event: Callable[[dict[str, Any]], None] | None = None
    if args.progress_events:
        def emit_event_fn(payload: dict[str, Any]) -> None:
            print(json.dumps(payload, ensure_ascii=False), flush=True)

        emit_event = emit_event_fn

    try:
        return asyncio.run(run_sync(dry_run=args.dry_run, limit=args.limit, emit_event=emit_event))
    except Exception as e:
        print(f"NetXP sync failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

