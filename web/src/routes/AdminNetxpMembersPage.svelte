<script lang="ts">
  import { onDestroy } from 'svelte'
  import { Link } from 'svelte-navigator'
  import { authReady, me, token } from '../stores/auth'
  import { syncNetxpMembers } from '../api/client'
  import {
    fetchMembers,
    membersActiveOnly,
    membersError,
    membersItems,
    membersLoading,
    membersPage,
    membersPageSize,
    membersSearch,
    membersTotal
  } from '../stores/members'
  import { get } from 'svelte/store'
  import commonStyles from '../styles/common.module.scss'

  function dateShort(v: string | null | undefined) {
    if (!v) return ''
    return v.length >= 10 ? v.slice(0, 10) : v
  }

  let membersTotalPagesValue = 1
  $: {
    const pages = Math.ceil($membersTotal / $membersPageSize)
    membersTotalPagesValue = pages > 0 ? pages : 1
  }

  let syncLoading = false
  let syncError: string | null = null
  let syncStatus: string | null = null
  let syncRunId: string | null = null
  let syncNotes: string | null = null
  let syncCounts = { inserted: 0, updated: 0, unchanged: 0, inactivated: 0, error: 0 }
  let syncAbort: AbortController | null = null

  onDestroy(() => {
    syncAbort?.abort()
  })

  async function runFetch() {
    const t = get(token)
    if (!t) return
    await fetchMembers(t)
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
    membersPage.set(1)
    await runFetch()
  }

  async function doPrev() {
    membersPage.set($membersPage - 1)
    await runFetch()
  }

  async function doNext() {
    membersPage.set($membersPage + 1)
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
        bind:value={$membersSearch}
        type="text"
        placeholder="name, netxp_id, member number"
      />
    </label>

    <label>
      Active only
      <input bind:checked={$membersActiveOnly} type="checkbox" />
    </label>

    <div class={commonStyles.row}>
      <button
        class={commonStyles.btnPrimary}
        disabled={$membersLoading}
        onclick={doSearch}
      >
        Search
      </button>
      <button
        class={commonStyles.btnSecondary}
        disabled={$membersLoading}
        onclick={runFetch}
      >
        Refresh
      </button>
    </div>

    <div class={commonStyles.row}>
      <button
        class={commonStyles.btnSecondary}
        disabled={syncLoading || $membersLoading}
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

    {#if $membersError}
      <p class={`${commonStyles.message} ${commonStyles.error}`}>{$membersError}</p>
    {/if}

    {#if $membersLoading}
      <p class={commonStyles.muted}>Loading...</p>
    {/if}

    {#if !$membersLoading && $membersItems.length > 0}
      <div class={commonStyles.tableFrame}>
        <table>
          <thead>
            <tr>
              <th>id</th>
              <th>netxp_id</th>
              <th>active</th>
              <th>first_seen_at</th>
              <th>last_seen_at</th>
              <th>inactive_since</th>
              <th>mitgliedsnummer</th>
              <th>vorname</th>
              <th>nachname</th>
              <th>geburtsdatum</th>
              <th>eintrittsdatum</th>
              <th>austrittsdatum</th>
              <th>mitgliedsart</th>
              <th>strasse</th>
              <th>plz</th>
              <th>ort</th>
              <th>telefon_privat</th>
              <th>telefon_arbeit</th>
              <th>email_privat</th>
              <th>nx_ssp_registration_code</th>
              <th>beitragsnamen</th>
              <th>info</th>
            </tr>
          </thead>
          <tbody>
            {#each $membersItems as m}
              <tr>
                <td>{m.id}</td>
                <td>{m.netxp_id}</td>
                <td>{m.is_active ? 'yes' : 'no'}</td>
                <td>{dateShort(m.first_seen_at)}</td>
                <td>{dateShort(m.last_seen_at)}</td>
                <td>{dateShort(m.inactive_since)}</td>
                <td>{m.mitgliedsnummer ?? ''}</td>
                <td>{m.vorname ?? ''}</td>
                <td>{m.nachname ?? ''}</td>
                <td>{dateShort(m.geburtsdatum)}</td>
                <td>{dateShort(m.eintrittsdatum)}</td>
                <td>{dateShort(m.austrittsdatum)}</td>
                <td>{m.mitgliedsart ?? ''}</td>
                <td>{m.strasse ?? ''}</td>
                <td>{m.plz ?? ''}</td>
                <td>{m.ort ?? ''}</td>
                <td>{m.telefon_privat ?? ''}</td>
                <td>{m.telefon_arbeit ?? ''}</td>
                <td>{m.email_privat ?? ''}</td>
                <td>{m.nx_ssp_registration_code ?? ''}</td>
                <td>{m.beitragsnamen ?? ''}</td>
                <td>{m.info ?? ''}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>

      <div class={commonStyles.paginationRow}>
        <button
          class={commonStyles.btnSecondary}
          disabled={$membersLoading || $membersPage <= 1}
          onclick={doPrev}
        >
          Prev
        </button>
        <button
          class={commonStyles.btnSecondary}
          disabled={$membersLoading || $membersPage >= membersTotalPagesValue}
          onclick={doNext}
        >
          Next
        </button>
      </div>

      <p class={commonStyles.muted}>
        Page {$membersPage} / {membersTotalPagesValue} (Total {$membersTotal})
      </p>
    {:else if !$membersLoading && !$membersError}
      <p class={commonStyles.muted}>No members found.</p>
    {/if}
  </section>
{/if}

