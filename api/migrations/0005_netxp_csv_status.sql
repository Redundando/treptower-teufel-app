-- 0005_netxp_csv_status.sql
-- NetXP CSV column "Status" as a typed column (distinct from is_active / sync-run status).

ALTER TABLE netxp_members
  ADD COLUMN IF NOT EXISTS csv_status TEXT NULL;

UPDATE netxp_members
SET csv_status = NULLIF(TRIM(netxp_raw->>'Status'), '')
WHERE netxp_raw ? 'Status';
