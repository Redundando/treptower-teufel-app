-- 0001_init.sql
-- Initial schema: members mirror + sync run tracking

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  netxp_id TEXT NOT NULL UNIQUE,

  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  inactive_since TIMESTAMPTZ NULL,

  mitgliedsnummer TEXT NULL,
  mitgliedsnummer_alphanummerisch TEXT NULL,
  vorname TEXT NULL,
  nachname TEXT NULL,
  geburtsdatum DATE NULL,
  eintrittsdatum DATE NULL,
  austrittsdatum DATE NULL,
  mitgliedsart TEXT NULL,
  strasse TEXT NULL,
  plz TEXT NULL,
  ort TEXT NULL,
  telefon_privat TEXT NULL,
  telefon_arbeit TEXT NULL,
  handy TEXT NULL,
  email_privat TEXT NULL,
  nx_ssp_registration_code TEXT NULL,
  beitragsnamen TEXT NULL,
  info TEXT NULL,

  netxp_raw JSONB NOT NULL DEFAULT '{}'::jsonb,
  netxp_raw_hash TEXT NULL,

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_members_is_active ON members (is_active);
CREATE INDEX IF NOT EXISTS idx_members_name ON members (nachname, vorname);

CREATE TABLE IF NOT EXISTS netxp_sync_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ NULL,
  status TEXT NOT NULL,

  source_url TEXT NULL,
  download_bytes BIGINT NULL,
  encoding_used TEXT NULL,
  delimiter TEXT NOT NULL DEFAULT ';',

  row_count INT NOT NULL DEFAULT 0,
  inserted_count INT NOT NULL DEFAULT 0,
  updated_count INT NOT NULL DEFAULT 0,
  unchanged_count INT NOT NULL DEFAULT 0,
  inactivated_count INT NOT NULL DEFAULT 0,
  error_count INT NOT NULL DEFAULT 0,

  headers JSONB NULL,
  file_hash TEXT NULL,
  notes TEXT NULL
);

