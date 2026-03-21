-- 0004_netxp_mitgliedsnummer_bigint.sql
-- Store NetXP membership number as integer; enables correct ORDER BY without text hacks.

ALTER TABLE netxp_members
  ALTER COLUMN mitgliedsnummer TYPE bigint
  USING (
    CASE
      WHEN mitgliedsnummer IS NULL THEN NULL
      WHEN regexp_replace(mitgliedsnummer::text, '[[:space:]]', '', 'g') = '' THEN NULL
      WHEN regexp_replace(mitgliedsnummer::text, '[[:space:]]', '', 'g') ~ '^[0-9]+$'
        THEN regexp_replace(mitgliedsnummer::text, '[[:space:]]', '', 'g')::bigint
      ELSE NULL
    END
  );
