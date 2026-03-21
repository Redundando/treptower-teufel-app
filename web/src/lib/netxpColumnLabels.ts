import * as m from '../paraglide/messages.js'

export type NetxpColId =
  | 'id'
  | 'netxp_id'
  | 'active'
  | 'first_seen_at'
  | 'last_seen_at'
  | 'inactive_since'
  | 'mitgliedsnummer'
  | 'vorname'
  | 'nachname'
  | 'geburtsdatum'
  | 'age'
  | 'eintrittsdatum'
  | 'member_years'
  | 'austrittsdatum'
  | 'mitgliedsart'
  | 'strasse'
  | 'plz'
  | 'ort'
  | 'telefon_privat'
  | 'telefon_arbeit'
  | 'email_privat'
  | 'nx_ssp_registration_code'
  | 'beitragsnamen'
  | 'info'
  | 'csv_status'

import type { NetxpMember } from '../types/netxpMember'

export function netxpColumnLabel(id: NetxpColId): string {
  switch (id) {
    case 'id':
      return m.netxp_col_internal_id()
    case 'netxp_id':
      return m.netxp_col_netxp_id()
    case 'active':
      return m.netxp_col_active()
    case 'first_seen_at':
      return m.netxp_col_first_seen()
    case 'last_seen_at':
      return m.netxp_col_last_seen()
    case 'inactive_since':
      return m.netxp_col_inactive_since()
    case 'mitgliedsnummer':
      return m.netxp_col_mitgliedsnummer()
    case 'vorname':
      return m.netxp_col_vorname()
    case 'nachname':
      return m.netxp_col_nachname()
    case 'geburtsdatum':
      return m.netxp_col_geburtsdatum()
    case 'age':
      return m.netxp_col_age()
    case 'eintrittsdatum':
      return m.netxp_col_eintrittsdatum()
    case 'member_years':
      return m.netxp_col_member_years()
    case 'austrittsdatum':
      return m.netxp_col_austrittsdatum()
    case 'mitgliedsart':
      return m.netxp_col_mitgliedsart()
    case 'strasse':
      return m.netxp_col_strasse()
    case 'plz':
      return m.netxp_col_plz()
    case 'ort':
      return m.netxp_col_ort()
    case 'telefon_privat':
      return m.netxp_col_telefon_privat()
    case 'telefon_arbeit':
      return m.netxp_col_telefon_arbeit()
    case 'email_privat':
      return m.netxp_col_email()
    case 'nx_ssp_registration_code':
      return m.netxp_col_ssp_code()
    case 'beitragsnamen':
      return m.netxp_col_beitragsnamen()
    case 'info':
      return m.netxp_col_info()
    case 'csv_status':
      return m.netxp_col_csv_status()
    default: {
      const _exhaustive: never = id
      return _exhaustive
    }
  }
}

export function netxpDetailLabel(key: keyof NetxpMember): string {
  switch (key) {
    case 'id':
      return m.netxp_col_internal_id()
    case 'netxp_id':
      return m.netxp_col_netxp_id()
    case 'is_active':
      return m.netxp_col_active()
    case 'first_seen_at':
      return m.netxp_col_first_seen()
    case 'last_seen_at':
      return m.netxp_col_last_seen()
    case 'inactive_since':
      return m.netxp_col_inactive_since()
    case 'mitgliedsnummer':
      return m.netxp_col_mitgliedsnummer()
    case 'vorname':
      return m.netxp_col_vorname()
    case 'nachname':
      return m.netxp_col_nachname()
    case 'geburtsdatum':
      return m.netxp_col_geburtsdatum()
    case 'eintrittsdatum':
      return m.netxp_col_eintrittsdatum()
    case 'austrittsdatum':
      return m.netxp_col_austrittsdatum()
    case 'mitgliedsart':
      return m.netxp_col_mitgliedsart()
    case 'strasse':
      return m.netxp_col_strasse()
    case 'plz':
      return m.netxp_col_plz()
    case 'ort':
      return m.netxp_col_ort()
    case 'telefon_privat':
      return m.netxp_col_telefon_privat()
    case 'telefon_arbeit':
      return m.netxp_col_telefon_arbeit()
    case 'email_privat':
      return m.netxp_col_email()
    case 'nx_ssp_registration_code':
      return m.netxp_col_ssp_code()
    case 'beitragsnamen':
      return m.netxp_col_beitragsnamen()
    case 'info':
      return m.netxp_col_info()
    case 'csv_status':
      return m.netxp_col_csv_status()
    case 'netxp_raw':
      return m.netxp_detail_netxp_raw()
    default:
      return String(key)
  }
}
