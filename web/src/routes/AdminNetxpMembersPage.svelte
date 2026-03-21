<script lang="ts">
  import { onDestroy } from 'svelte'
  import { Link } from 'svelte-navigator'
  import { authReady, me, token } from '../../stores/auth'
  import { syncNetxpMembers } from '../../api/client'
  import {
    fetchNetxpMembers,
    netxpMembersActiveOnly,
    netxpMembersCurrentOnly,
    netxpMembersError,
    netxpMembersItems,
    netxpMembersLoading,
    netxpMembersPage,
    netxpMembersPageSize,
    netxpMembersSearch,
    netxpMembersTotal
  } from '../../stores/netxpMembers'
  import { get } from 'svelte/store'
  import type { NetxpMember } from '../../types/netxpMember'
  import commonStyles from '../../styles/common.module.scss'
  import pageStyles from './AdminNetxpMembersPage.module.scss'

  const COL_STORAGE_KEY = 'tttc-admin-netxp-member-cols-v1'

  type ColId =
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
    | 'eintrittsdatum'
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

  type ColDef = { id: ColId; label: string; defaultVisible: boolean }

  /** Order = table column order. Only `defaultVisible` columns show until the user changes preferences. */
  const COL_DEFS: ColDef[] = [
    { id: 'id', label: 'Internal id', defaultVisible: false },
    { id: 'netxp_id', label: 'NetXP id', defaultVisible: true },
    { id: 'active', label: 'Active', defaultVisible: true },
    { id: 'first_seen_at', label: 'First seen', defaultVisible: false },
    { id: 'last_seen_at', label: 'Last seen', defaultVisible: false },
    { id: 'inactive_since', label: 'Inactive since', defaultVisible: false },
    { id: 'mitgliedsnummer', label: 'Mitgliedsnummer', defaultVisible: true },
    { id: 'vorname', label: 'Vorname', defaultVisible: true },
    { id: 'nachname', label: 'Nachname', defaultVisible: true },
    { id: 'geburtsdatum', label: 'Geburtsdatum', defaultVisible: true },
    { id: 'eintrittsdatum', label: 'Eintrittsdatum', defaultVisible: true },
    { id: 'austrittsdatum', label: 'Austrittsdatum', defaultVisible: true },
    { id: 'mitgliedsart', label: 'Mitgliedsart', defaultVisible: true },
    { id: 'strasse', label: 'Straße', defaultVisible: true },
    { id: 'plz', label: 'PLZ', defaultVisible: true },
    { id: 'ort', label: 'Ort', defaultVisible: true },
    { id: 'telefon_privat', label: 'Telefon (privat)', defaultVisible: true },
    { id: 'telefon_arbeit', label: 'Telefon (Arbeit)', defaultVisible: true },
    { id: 'email_privat', label: 'E-Mail', defaultVisible: true },
    { id: 'nx_ssp_registration_code', label: 'SSP registration code', defaultVisible: false },
    { id: 'beitragsnamen', label: 'Beitragsnamen', defaultVisible: true },
    { id: 'info', label: 'Info', defaultVisible: false }
  ]

  function defaultVisibleColIds(): ColId[] {
    return COL_DEFS.filter((c) => c.defaultVisible).map((c) => c.id)
  }

  function loadColumnPrefs(): ColId[] {
    if (typeof localStorage === 'undefined') return defaultVisibleColIds()
    try {
      const raw = localStorage.getItem(COL_STORAGE_KEY)
      if (!raw) return defaultVisibleColIds()
      const parsed = JSON.parse(raw) as unknown
      if (!Array.isArray(parsed)) return defaultVisibleColIds()
      const allowed = new Set(COL_DEFS.map((c) => c.id))
      const next = parsed.filter((x): x is ColId => typeof x === 'string' && allowed.has(x as ColId))
      return next.length > 0 ? next : defaultVisibleColIds()
    } catch {
      return defaultVisibleColIds()
    }
  }

  function saveColumnPrefs(ids: ColId[]) {
    try {
      localStorage.setItem(COL_STORAGE_KEY, JSON.stringify(ids))
    } catch {
      /* ignore quota / private mode */
    }
  }

  let visibleColIds = $state<ColId[]>(loadColumnPrefs())

  let orderedVisibleCols = $derived(COL_DEFS.filter((c) => visibleColIds.includes(c.id)))

  $effect(() => {
    saveColumnPrefs(visibleColIds)
  })

  function resetColumnsToDefault() {
    visibleColIds = [...defaultVisibleColIds()]
  }

  function dateShort(v: string | null | undefined) {
    if (!v) return ''
    return v.length >= 10 ? v.slice(0, 10) : v
  }

  function cellValue(m: NetxpMember, id: ColId): string {
    switch (id) {
      case 'active':
        return m.is_active ? 'yes' : 'no'
      case 'geburtsdatum':
      case 'eintrittsdatum':
      case 'austrittsdatum':
      case 'first_seen_at':
      case 'last_seen_at':
      case 'inactive_since':
        return dateShort(m[id])
      default: {
        const v = m[id as keyof NetxpMember]
        return v == null || v === '' ? '' : String(v)
      }
    }
  }

  let netxpMembersTotalPagesValue = $derived(
    Math.max(1, Math.ceil($netxpMembersTotal / $netxpMembersPageSize))
  )

  let syncLoading = $state(false)
  let syncError = $state<string | null>(null)
  let syncStatus = $state<string | null>(null)
  let syncRunId = $state<string | null>(null)
  let syncNotes = $state<string | null>(null)
  let syncCounts = $state({
    inserted: 0,
    updated: 0,
    unchanged: 0,
    inactivated: 0,
    error: 0
  })
  let syncAbort: AbortController | null = null

  onDestroy(() => {
    syncAbort?.abort()
  })

  async function runFetch() {
    const t = get(token)
    if (!t) return
    await fetchNetxpMembers(t)
  }

  async function startNetxpSync() {
    const t = get(token)
    if (!t || syncLoading) return

    syncLoading = true
    syncError = null
    syncStatus = 'Starting NetXP sync...'
    syncRunId = null
    syncNotes = null
    syncCounts = { inserted: 0, updated: 0, unchanged: 0, inactivated: 0, error: 0 }

    const started = await syncNetxpMembers(t)

    const controller = new AbortController()
    syncAbort = controller

    try {
      syncRunId = started.job_id

      const resp = await fetch(`/api/job/${started.job_id}/stream`, {
        headers: { Authorization: `Bearer ${t}` },
        signal: controller.signal
      })

      if (!resp.ok) {
        let detail: string | undefined
        try {
          const j = (await resp.json()) as { detail?: string }
          detail = j?.detail
        } catch {
          detail = undefined
        }
        throw new Error(detail ?? `Sync stream failed (${resp.status})`)
      }

      if (!resp.body) throw new Error('Missing SSE response body')

      const reader = resp.body.getReader()
      const decoder = new TextDecoder('utf-8')

      let buf = ''
      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        buf += decoder.decode(value, { stream: true })

        while (true) {
          const sepIdx = buf.indexOf('\n\n')
          if (sepIdx === -1) break

          const rawEvent = buf.slice(0, sepIdx).trim()
          buf = buf.slice(sepIdx + 2)

          if (!rawEvent) continue

          const lines = rawEvent.split('\n')
          const dataLines: string[] = []
          for (const line of lines) {
            if (line.startsWith('data:')) {
              dataLines.push(line.slice(5).trimStart())
            }
          }
          if (dataLines.length === 0) continue

          const dataStr = dataLines.join('\n')
          let payload: any
          try {
            payload = JSON.parse(dataStr)
          } catch {
            continue
          }

          if (payload.event === 'netxp_sync_started') {
            syncStatus = 'running'
            continue
          }

          if (payload.event === 'netxp_sync_download_and_parse_done') {
            syncStatus = 'download + parse done'
            continue
          }

          if (payload.event === 'netxp_sync_diff_counts') {
            syncCounts = {
              inserted: payload.inserted ?? 0,
              updated: payload.updated ?? 0,
              unchanged: payload.unchanged ?? 0,
              inactivated: syncCounts.inactivated,
              error: syncCounts.error
            }
            continue
          }

          if (payload.event === 'netxp_sync_dry_run_done') {
            syncStatus = 'dry_run'
            syncCounts = {
              inserted: payload.inserted ?? 0,
              updated: payload.updated ?? 0,
              unchanged: payload.unchanged ?? 0,
              inactivated: payload.inactivated ?? 0,
              error: payload.error_count ?? 0
            }
            syncNotes = null
            return
          }

          if (payload.event === 'netxp_sync_success') {
            syncStatus = 'success'
            syncCounts = {
              inserted: payload.inserted ?? 0,
              updated: payload.updated ?? 0,
              unchanged: payload.unchanged ?? 0,
              inactivated: payload.inactivated ?? 0,
              error: payload.error_count ?? 0
            }
            syncNotes = null
            return
          }

          if (payload.event === 'netxp_sync_failed') {
            syncStatus = 'failed'
            syncNotes = payload.error ?? null
            syncCounts = {
              inserted: syncCounts.inserted,
              updated: syncCounts.updated,
              unchanged: syncCounts.unchanged,
              inactivated: syncCounts.inactivated,
              error: syncCounts.error
            }
            return
          }

          if (payload.event === 'done') {
            return
          }
        }
      }
    } catch (e) {
      syncError = e instanceof Error ? e.message : 'NetXP sync failed'
    } finally {
      syncLoading = false
      syncAbort = null
      await runFetch()
    }
  }

  async function doSearch() {
    netxpMembersPage.set(1)
    await runFetch()
  }

  async function doPrev() {
    netxpMembersPage.set($netxpMembersPage - 1)
    await runFetch()
  }

  async function doNext() {
    netxpMembersPage.set($netxpMembersPage + 1)
    await runFetch()
  }
</script>

{#if !$authReady}
  <section class={commonStyles.card}>
    <p class={commonStyles.muted}>Loading...</p>
  </section>
{:else if $me?.role !== 'admin'}
  <section class={commonStyles.card}>
    <h2>Admin only</h2>
    <p class={commonStyles.muted}>You need an admin account for this route.</p>
    <div class={commonStyles.row}>
      <Link class={commonStyles.btnSecondary} to="/">Back to Index</Link>
    </div>
  </section>
{:else}
  <section class={commonStyles.card}>
    <h2>Admin: NetXP Members</h2>

    <label>
      Search
      <input
        bind:value={$netxpMembersSearch}
        type="text"
        placeholder="name, netxp_id, member number"
      />
    </label>

    <label>
      Active only
      <input
        type="checkbox"
        checked={$netxpMembersActiveOnly}
        onchange={(e) => netxpMembersActiveOnly.set(e.currentTarget.checked)}
      />
    </label>

    <label>
      Current members (by Austrittsdatum)
      <input
        type="checkbox"
        checked={$netxpMembersCurrentOnly}
        onchange={(e) => netxpMembersCurrentOnly.set(e.currentTarget.checked)}
      />
    </label>
    <p class={pageStyles.filterNote}>
      When enabled: only people with <strong>no</strong> exit date, or an exit date <strong>after today</strong>
      (still in the club according to that field). Past exit dates are excluded.
    </p>

    <div class={commonStyles.row}>
      <button
        class={commonStyles.btnPrimary}
        disabled={$netxpMembersLoading}
        onclick={doSearch}
      >
        Search
      </button>
      <button
        class={commonStyles.btnSecondary}
        disabled={$netxpMembersLoading}
        onclick={runFetch}
      >
        Refresh
      </button>
    </div>

    <div class={commonStyles.row}>
      <button
        class={commonStyles.btnSecondary}
        disabled={syncLoading || $netxpMembersLoading}
        onclick={startNetxpSync}
      >
        {syncLoading ? 'Syncing NetXP...' : 'Import/Update from NetXP'}
      </button>
    </div>

    {#if syncError}
      <p class={`${commonStyles.message} ${commonStyles.error}`}>{syncError}</p>
    {/if}

    {#if syncStatus}
      <p class={commonStyles.muted}>
        NetXP sync: {syncStatus}{syncRunId ? ` (${syncRunId})` : ''}
      </p>
    {/if}

    {#if syncStatus === 'success' || syncStatus === 'failed' || syncStatus === 'dry_run'}
      <p class={commonStyles.muted}>
        inserted {syncCounts.inserted}, updated {syncCounts.updated}, unchanged {syncCounts.unchanged},
        inactivated {syncCounts.inactivated}, errors {syncCounts.error}
      </p>
      {#if syncNotes}
        <p class={commonStyles.muted}>{syncNotes}</p>
      {/if}
    {/if}

    {#if $netxpMembersError}
      <p class={`${commonStyles.message} ${commonStyles.error}`}>{$netxpMembersError}</p>
    {/if}

    <details class={pageStyles.columnPanel}>
      <summary>Table columns</summary>
      <p class={`${commonStyles.muted} ${pageStyles.columnHint}`}>
        Shown by default: membership and contact fields. Turn on extra columns when you need sync metadata,
        internal ids, registration codes, or long info text. Your choices are saved in this browser.
      </p>
      <div class={pageStyles.columnActions}>
        <button type="button" class={commonStyles.btnSecondary} onclick={resetColumnsToDefault}>
          Reset to defaults
        </button>
      </div>
      <div class={pageStyles.columnGrid}>
        {#each COL_DEFS as col}
          <label>
            <input type="checkbox" bind:group={visibleColIds} value={col.id} />
            {col.label}
          </label>
        {/each}
      </div>
    </details>

    {#if $netxpMembersLoading}
      <p class={commonStyles.muted}>Loading...</p>
    {/if}

    {#if !$netxpMembersLoading && $netxpMembersItems.length > 0}
      <div class={commonStyles.tableFrame}>
        <table>
          <thead>
            <tr>
              {#each orderedVisibleCols as col}
                <th>{col.label}</th>
              {/each}
            </tr>
          </thead>
          <tbody>
            {#each $netxpMembersItems as m}
              <tr>
                {#each orderedVisibleCols as col}
                  <td>{cellValue(m, col.id)}</td>
                {/each}
              </tr>
            {/each}
          </tbody>
        </table>
      </div>

      <div class={commonStyles.paginationRow}>
        <button
          class={commonStyles.btnSecondary}
          disabled={$netxpMembersLoading || $netxpMembersPage <= 1}
          onclick={doPrev}
        >
          Prev
        </button>
        <button
          class={commonStyles.btnSecondary}
          disabled={$netxpMembersLoading || $netxpMembersPage >= netxpMembersTotalPagesValue}
          onclick={doNext}
        >
          Next
        </button>
      </div>

      <p class={commonStyles.muted}>
        Page {$netxpMembersPage} / {netxpMembersTotalPagesValue} (Total {$netxpMembersTotal})
      </p>
    {:else if !$netxpMembersLoading && !$netxpMembersError}
      <p class={commonStyles.muted}>No NetXP members found.</p>
    {/if}
  </section>
{/if}

