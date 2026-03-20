-- 0002_rename_members_to_netxp_members.sql
-- v1 naming clarity: store NetXP data in `netxp_members` (not generic `members`)

ALTER TABLE members RENAME TO netxp_members;

-- Optional: rename indexes to match the new table name for easier debugging.
ALTER INDEX IF EXISTS idx_members_is_active RENAME TO idx_netxp_members_is_active;
ALTER INDEX IF EXISTS idx_members_name RENAME TO idx_netxp_members_name;

