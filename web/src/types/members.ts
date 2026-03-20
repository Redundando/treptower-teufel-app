export type NetxpMember = {
  id: string
  netxp_id: string
  is_active: boolean
  first_seen_at: string
  last_seen_at: string
  inactive_since: string | null
  mitgliedsnummer: string | null
  vorname: string | null
  nachname: string | null
  geburtsdatum: string | null
  eintrittsdatum: string | null
  austrittsdatum: string | null
  mitgliedsart: string | null
  strasse: string | null
  plz: string | null
  ort: string | null
  telefon_privat: string | null
  telefon_arbeit: string | null
  email_privat: string | null
  nx_ssp_registration_code: string | null
  beitragsnamen: string | null
  info: string | null
}

