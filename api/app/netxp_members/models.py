from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator


def mitgliedsnummer_from_db(v: Any) -> Any:
    """BIGINT from asyncpg (int) or legacy text; never leave as str for JSON number."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        try:
            return int(s)
        except ValueError:
            return None
    if isinstance(v, Decimal):
        return int(v)
    return v


class NetxpMemberOut(BaseModel):
    id: str
    netxp_id: str

    is_active: bool
    first_seen_at: datetime
    last_seen_at: datetime
    inactive_since: datetime | None

    # DB column is BIGINT (asyncpg → int). Use plain int + field_validator (not Annotated) so schema is never str.
    mitgliedsnummer: int | None = None
    vorname: str | None = None
    nachname: str | None = None
    geburtsdatum: date | None = None
    eintrittsdatum: date | None = None
    austrittsdatum: date | None = None
    mitgliedsart: str | None = None
    strasse: str | None = None
    plz: str | None = None
    ort: str | None = None
    telefon_privat: str | None = None
    telefon_arbeit: str | None = None
    email_privat: str | None = None
    nx_ssp_registration_code: str | None = None
    beitragsnamen: str | None = None
    info: str | None = None
    csv_status: str | None = None

    netxp_raw: dict[str, Any] = Field(default_factory=dict)

    @field_validator("mitgliedsnummer", mode="before")
    @classmethod
    def _mitgliedsnummer_int(cls, v: Any) -> Any:
        return mitgliedsnummer_from_db(v)


class NetxpSyncStartResponse(BaseModel):
    job_id: str
