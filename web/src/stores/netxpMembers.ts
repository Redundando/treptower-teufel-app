import { get, writable } from 'svelte/store'

import type { NetxpMember } from '../types/netxpMember'

import { fetchNetxpMembers as fetchNetxpMembersApi } from '../api/client'

import { loadNetxpViewPrefsWithMigration } from '../lib/netxpViewPrefs'

import { normalizeNetxpPageSize } from '../lib/netxpMembersPageSizeCookie'

export type { NetxpPageSizeOption } from '../lib/netxpMembersPageSizeCookie'

export { NETXP_PAGE_SIZE_OPTIONS } from '../lib/netxpMembersPageSizeCookie'

const initial = loadNetxpViewPrefsWithMigration()

export const netxpMembersLoading = writable(false)

export const netxpMembersError = writable<string | null>(null)

export const netxpMembersPage = writable(1)

export const netxpMembersPageSize = writable(initial.pageSize)

/** Updates store only; cookie persistence runs from AdminNetxpMembersPage prefs effect. */

export function persistNetxpMembersPageSize(size: number): void {
  netxpMembersPageSize.set(normalizeNetxpPageSize(size))
}

export const netxpMembersTotal = writable(0)

export const netxpMembersItems = writable<NetxpMember[]>([])

export const netxpMembersSearch = writable(initial.search)

export const netxpMembersActiveOnly = writable(initial.activeOnly)

/** No exit date or Austrittsdatum after today (see API `current_members_only`). */

export const netxpMembersCurrentOnly = writable(initial.currentOnly)

/** At most 18 on Jan 1 of current year (server); see API `youth_only`. */

export const netxpMembersYouthOnly = writable(initial.youthOnly ?? false)

/** NetXP CSV `csv_status` filter: restrict to aktiv and/or passiv (see API `csv_status_aktiv` / `csv_status_passiv`). */

export const netxpMembersCsvStatusAktiv = writable(initial.csvStatusAktiv ?? false)

export const netxpMembersCsvStatusPassiv = writable(initial.csvStatusPassiv ?? false)

/** API `sort_by` (ColId); null = default name order on server. */

export const netxpMembersSortBy = writable<string | null>(initial.sortBy)

export const netxpMembersSortDir = writable<'asc' | 'desc'>(initial.sortDir)

/** Clears list/session state only; preserves user prefs (filters, sort, page size, etc.). */

export function resetNetxpMembersState() {
  netxpMembersLoading.set(false)

  netxpMembersError.set(null)

  netxpMembersPage.set(1)

  netxpMembersTotal.set(0)

  netxpMembersItems.set([])
}

/** Optional `sort` avoids any edge case where the request runs before store writes are visible. */

export async function fetchNetxpMembers(
  token: string,
  sort?: { by: string; dir: 'asc' | 'desc' },
  opts?: { youthOnly?: boolean }
) {
  if (!token) return

  netxpMembersLoading.set(true)

  netxpMembersError.set(null)

  try {
    const page = get(netxpMembersPage)

    const pageSize = get(netxpMembersPageSize)

    const activeOnly = get(netxpMembersActiveOnly)

    const search = get(netxpMembersSearch)

    const currentMembersOnly = get(netxpMembersCurrentOnly)

    const youthOnly = opts?.youthOnly ?? get(netxpMembersYouthOnly)

    const csvStatusAktiv = get(netxpMembersCsvStatusAktiv)

    const csvStatusPassiv = get(netxpMembersCsvStatusPassiv)

    const sortBy = sort?.by ?? get(netxpMembersSortBy)

    const sortDir = sort?.dir ?? get(netxpMembersSortDir)

    const j = await fetchNetxpMembersApi(token, {
      page,
      pageSize,
      activeOnly,
      search,
      currentMembersOnly,
      youthOnly,
      csvStatusAktiv,
      csvStatusPassiv,
      sortBy,
      sortDir
    })

    netxpMembersPage.set(j.page)

    netxpMembersPageSize.set(normalizeNetxpPageSize(j.page_size))

    netxpMembersTotal.set(j.total)

    // New array reference so dependents always see a list reorder (e.g. sort_by=csv_status).
    netxpMembersItems.set([...j.items])
  } catch (e) {
    netxpMembersError.set(e instanceof Error ? e.message : 'Network error')
  } finally {
    netxpMembersLoading.set(false)
  }
}
