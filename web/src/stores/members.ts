import { get, writable } from 'svelte/store'
import type { NetxpMember } from '../types/members'
import { fetchMembers as fetchMembersApi } from '../api/client'

export const membersLoading = writable(false)
export const membersError = writable<string | null>(null)

export const membersPage = writable(1)
export const membersPageSize = writable(20)
export const membersTotal = writable(0)
export const membersItems = writable<NetxpMember[]>([])

export const membersSearch = writable('')
export const membersActiveOnly = writable(true)

export function resetMembersState() {
  membersLoading.set(false)
  membersError.set(null)
  membersPage.set(1)
  membersPageSize.set(20)
  membersTotal.set(0)
  membersItems.set([])
  membersSearch.set('')
  membersActiveOnly.set(true)
}

export async function fetchMembers(token: string) {
  if (!token) return

  membersLoading.set(true)
  membersError.set(null)

  try {
    const page = get(membersPage)
    const pageSize = get(membersPageSize)
    const activeOnly = get(membersActiveOnly)
    const search = get(membersSearch)

    const j = await fetchMembersApi(token, { page, pageSize, activeOnly, search })

    membersPage.set(j.page)
    membersPageSize.set(j.page_size)
    membersTotal.set(j.total)
    membersItems.set(j.items)
  } catch (e) {
    membersError.set(e instanceof Error ? e.message : 'Network error')
  } finally {
    membersLoading.set(false)
  }
}

