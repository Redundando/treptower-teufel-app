"""Column name contracts for `netxp_members` (aligned with DB schema / migrations)."""

from __future__ import annotations

TYPED_COLUMNS: list[str] = [
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

# DB column names allowed in ORDER BY (plus UI aliases handled in query.order_sql).
NETXP_MEMBER_SORTABLE_DB: frozenset[str] = frozenset(
    {
        "id",
        "netxp_id",
        "is_active",
        "first_seen_at",
        "last_seen_at",
        "inactive_since",
        *TYPED_COLUMNS,
    }
)

EXPORT_FIELDNAMES: list[str] = [
    "id",
    "netxp_id",
    "is_active",
    "first_seen_at",
    "last_seen_at",
    "inactive_since",
    *TYPED_COLUMNS,
    "netxp_raw_json",
]

# NetXP admin table column ids (see web NetxpColId); used when ?columns= is passed.
ALLOWED_VISUAL_EXPORT_COL_IDS: frozenset[str] = frozenset(
    {
        "id",
        "netxp_id",
        "active",
        "first_seen_at",
        "last_seen_at",
        "inactive_since",
        "mitgliedsnummer",
        "vorname",
        "nachname",
        "geburtsdatum",
        "age",
        "eintrittsdatum",
        "member_years",
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
    }
)
