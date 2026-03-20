import { get, writable } from 'svelte/store'
import type { Me, Role } from '../types/auth'
import { adminCreateUser as adminCreateUserApi, checkApi, fetchMe, login as loginApi } from '../api/client'
import { fetchMembers, resetMembersState } from './members'

const STORAGE_KEY = 'access_token'

export const token = writable<string | null>(null)
export const me = writable<Me | null>(null)
export const authReady = writable(false)
export const apiStatus = writable('API: …')

// Incrementing this triggers redirect in the root App component.
export const redirectToIndex = writable(0)

function loadTokenFromStorage(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
}

function saveTokenToStorage(v: string | null) {
  try {
    if (!v) localStorage.removeItem(STORAGE_KEY)
    else localStorage.setItem(STORAGE_KEY, v)
  } catch {
    // ignore storage failures
  }
}

export function logout() {
  token.set(null)
  me.set(null)
  authReady.set(true)

  resetMembersState()

  saveTokenToStorage(null)

  redirectToIndex.update((n) => n + 1)
}

export async function bootstrapAuth() {
  authReady.set(false)

  const t = loadTokenFromStorage()
  token.set(t)

  apiStatus.set(await checkApi())

  if (!t) {
    authReady.set(true)
    return
  }

  try {
    const j = await fetchMe(t)
    me.set(j)

    if (j.role === 'admin') {
      // Preserve current behavior: preload members for admins on bootstrap.
      await fetchMembers(t)
    }
  } catch {
    // Invalid/expired token.
    logout()
  } finally {
    authReady.set(true)
  }
}

export async function login(email: string, password: string) {
  apiStatus.set(get(apiStatus))

  const j = await loginApi(email, password)

  const t = j.access_token
  token.set(t)
  saveTokenToStorage(t)

  try {
    const meJson = await fetchMe(t)
    me.set(meJson)

    if (meJson.role === 'admin') {
      // Preserve current behavior: preload members for admins after login.
      await fetchMembers(t)
    }
  } catch {
    logout()
    return
  }

  redirectToIndex.update((n) => n + 1)
}

export async function adminCreateUser(payload: { email: string; password: string; role: Role }) {
  const t = get(token)
  if (!t) throw new Error('Not authenticated')

  const j = await adminCreateUserApi(t, payload)
  return `Created user ${j.email} (${j.role})`
}

