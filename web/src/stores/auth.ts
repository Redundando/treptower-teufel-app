import { get, writable } from 'svelte/store'
import type { Me, Role } from '../types/auth'
import { admin_create_success } from '../paraglide/messages.js'
import {
  clearAuthTokenCookie,
  readAuthTokenFromCookie,
  writeAuthTokenToCookie
} from '../lib/authTokenCookie'
import { adminCreateUser as adminCreateUserApi, fetchMe, login as loginApi } from '../api/client'
import { fetchNetxpMembers, resetNetxpMembersState } from './netxpMembers'

/** Legacy localStorage key — migrated to cookie on first load */
const LEGACY_STORAGE_KEY = 'access_token'

export const token = writable<string | null>(null)
export const me = writable<Me | null>(null)
export const authReady = writable(false)

// Incrementing this triggers redirect in the root App component.
export const redirectToIndex = writable(0)

function loadTokenFromStorage(): string | null {
  const fromCookie = readAuthTokenFromCookie()
  if (fromCookie) return fromCookie

  try {
    const legacy = localStorage.getItem(LEGACY_STORAGE_KEY)
    if (!legacy) return null
    writeAuthTokenToCookie(legacy)
    localStorage.removeItem(LEGACY_STORAGE_KEY)
    return legacy
  } catch {
    return null
  }
}

function saveTokenToStorage(v: string | null) {
  try {
    if (!v) {
      clearAuthTokenCookie()
      localStorage.removeItem(LEGACY_STORAGE_KEY)
    } else {
      writeAuthTokenToCookie(v)
      try {
        localStorage.removeItem(LEGACY_STORAGE_KEY)
      } catch {
        // ignore
      }
    }
  } catch {
    // ignore storage failures
  }
}

export function logout() {
  token.set(null)
  me.set(null)
  authReady.set(true)

  resetNetxpMembersState()

  saveTokenToStorage(null)

  redirectToIndex.update((n) => n + 1)
}

export async function bootstrapAuth() {
  authReady.set(false)

  const t = loadTokenFromStorage()
  token.set(t)

  if (!t) {
    authReady.set(true)
    return
  }

  try {
    const j = await fetchMe(t)
    me.set(j)

    if (j.role === 'admin') {
      await fetchNetxpMembers(t)
    }
  } catch {
    // Invalid/expired token.
    logout()
  } finally {
    authReady.set(true)
  }
}

export async function login(email: string, password: string) {
  const j = await loginApi(email, password)

  const t = j.access_token
  token.set(t)
  saveTokenToStorage(t)

  try {
    const meJson = await fetchMe(t)
    me.set(meJson)

    if (meJson.role === 'admin') {
      await fetchNetxpMembers(t)
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
  return admin_create_success({ email: j.email, role: j.role })
}

