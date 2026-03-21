<script lang="ts">

  import { onDestroy, onMount } from 'svelte'

  import { Link } from 'svelte-navigator'

  import { authReady, me, token } from '../../../stores/auth'

  import { exportNetxpMembersCsv, exportNetxpMembersXlsx, syncNetxpMembers } from '../../../api/client'

  import {

    fetchNetxpMembers,

    netxpMembersActiveOnly,

    netxpMembersCurrentOnly,

    netxpMembersYouthOnly,

    netxpMembersCsvStatusAktiv,

    netxpMembersCsvStatusPassiv,

    netxpMembersError,

    netxpMembersItems,

    netxpMembersLoading,

    netxpMembersPage,

    netxpMembersPageSize,

    netxpMembersSearch,

    netxpMembersSortBy,

    netxpMembersSortDir,

    netxpMembersTotal,

    NETXP_PAGE_SIZE_OPTIONS,

    persistNetxpMembersPageSize

  } from '../../../stores/netxpMembers'

  import { get } from 'svelte/store'

  import type { NetxpMember } from '../../../types/netxpMember'

  import commonStyles from '../../../styles/common.module.scss'

  import pageStyles from './AdminNetxpMembersPage.module.scss'

  import { ColumnPicker, DataTable, PageSizeSelect } from '../../../components/data-table'

  import type { DataTableColumnDef } from '../../../components/data-table'

  import NetxpMembersFilters from './NetxpMembersFilters.svelte'

  import {

    buildNetxpViewPrefsFromStores,

    loadNetxpViewPrefsWithMigration,

    writeNetxpViewPrefsCookie

  } from '../../../lib/netxpViewPrefs'

  import * as m from '../../../paraglide/messages.js'

  import { translateClientErrorMessage } from '../../../lib/apiErrorMessage'

  import { netxpSyncStatusLabel } from '../../../lib/netxpSyncLabels'

  import { netxpColumnLabel, netxpDetailLabel, type NetxpColId } from '../../../lib/netxpColumnLabels'

  type ColId = NetxpColId

  type ColDef = { id: ColId; defaultVisible: boolean }



  const initialPrefs = loadNetxpViewPrefsWithMigration()



  const COL_DEFS: ColDef[] = [

    { id: 'id', defaultVisible: false },

    { id: 'netxp_id', defaultVisible: false },

    { id: 'active', defaultVisible: false },

    { id: 'first_seen_at', defaultVisible: false },

    { id: 'last_seen_at', defaultVisible: false },

    { id: 'inactive_since', defaultVisible: false },

    { id: 'mitgliedsnummer', defaultVisible: true },

    { id: 'vorname', defaultVisible: true },

    { id: 'nachname', defaultVisible: true },

    { id: 'geburtsdatum', defaultVisible: true },

    { id: 'age', defaultVisible: true },

    { id: 'eintrittsdatum', defaultVisible: true },

    { id: 'member_years', defaultVisible: true },

    { id: 'austrittsdatum', defaultVisible: false },

    { id: 'mitgliedsart', defaultVisible: false },

    { id: 'csv_status', defaultVisible: false },

    { id: 'strasse', defaultVisible: false },

    { id: 'plz', defaultVisible: false },

    { id: 'ort', defaultVisible: false },

    { id: 'telefon_privat', defaultVisible: false },

    { id: 'telefon_arbeit', defaultVisible: false },

    { id: 'email_privat', defaultVisible: true },

    { id: 'nx_ssp_registration_code', defaultVisible: false },

    { id: 'beitragsnamen', defaultVisible: false },

    { id: 'info', defaultVisible: false }

  ]



  function defaultVisibleColIds(): ColId[] {

    return COL_DEFS.filter((c) => c.defaultVisible).map((c) => c.id)

  }



  function loadColumnPrefs(): ColId[] {

    const cols = initialPrefs.cols

    if (!cols.length) return defaultVisibleColIds()

    const allowed = new Set(COL_DEFS.map((c) => c.id))

    const next = cols.filter((x): x is ColId => typeof x === 'string' && allowed.has(x as ColId))

    return next.length > 0 ? next : defaultVisibleColIds()

  }



  let visibleColIds = $state<ColId[]>(loadColumnPrefs())



  let orderedVisibleCols = $derived(COL_DEFS.filter((c) => visibleColIds.includes(c.id)))



  let tableColumns = $derived<DataTableColumnDef[]>(

    orderedVisibleCols.map((c) => ({ id: c.id, label: netxpColumnLabel(c.id) }))

  )



  let canPersistPrefs = $state(false)

  let persistTimer: ReturnType<typeof setTimeout> | null = null



  function schedulePersistPrefs() {

    if (!canPersistPrefs) return

    if (persistTimer) clearTimeout(persistTimer)

    persistTimer = setTimeout(() => {

      persistTimer = null

      writeNetxpViewPrefsCookie(

        buildNetxpViewPrefsFromStores(

          {

            pageSize: get(netxpMembersPageSize),

            search: get(netxpMembersSearch),

            activeOnly: get(netxpMembersActiveOnly),

            currentOnly: get(netxpMembersCurrentOnly),

            youthOnly: get(netxpMembersYouthOnly),

            csvStatusAktiv: get(netxpMembersCsvStatusAktiv) === true,

            csvStatusPassiv: get(netxpMembersCsvStatusPassiv) === true,

            sortBy: get(netxpMembersSortBy),

            sortDir: get(netxpMembersSortDir)

          },

          visibleColIds as string[]

        )

      )

    }, 150)

  }



  $effect(() => {

    void $netxpMembersPageSize

    void $netxpMembersSearch

    void $netxpMembersActiveOnly

    void $netxpMembersCurrentOnly

    void $netxpMembersYouthOnly

    void $netxpMembersCsvStatusAktiv

    void $netxpMembersCsvStatusPassiv

    void $netxpMembersSortBy

    void $netxpMembersSortDir

    void visibleColIds

    schedulePersistPrefs()

  })



  onMount(() => {

    canPersistPrefs = true

    return () => {

      canPersistPrefs = false

      if (persistTimer) clearTimeout(persistTimer)

    }

  })



  function resetColumnsToDefault() {

    visibleColIds = [...defaultVisibleColIds()]

  }



  async function sortByColumn(colId: ColId) {

    const t = get(token)

    if (!t) return

    const cur = get(netxpMembersSortBy)

    let dir: 'asc' | 'desc'

    if (cur === colId) {

      dir = get(netxpMembersSortDir) === 'asc' ? 'desc' : 'asc'

      netxpMembersSortDir.set(dir)

    } else {

      dir = 'asc'

      netxpMembersSortBy.set(colId)

      netxpMembersSortDir.set(dir)

    }

    netxpMembersPage.set(1)

    await fetchNetxpMembers(t, { by: colId, dir })

  }



  function dateShort(v: string | null | undefined) {

    if (!v) return ''

    return v.length >= 10 ? v.slice(0, 10) : v

  }



  function parseIsoDateOnly(raw: string | null | undefined): Date | null {

    if (!raw) return null

    const d = raw.trim().slice(0, 10)

    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(d)

    if (!m) return null

    const y = Number(m[1])

    const mo = Number(m[2]) - 1

    const da = Number(m[3])

    const dt = new Date(y, mo, da)

    if (dt.getFullYear() !== y || dt.getMonth() !== mo || dt.getDate() !== da) return null

    return dt

  }



  function startOfTodayLocal(): Date {

    const n = new Date()

    return new Date(n.getFullYear(), n.getMonth(), n.getDate())

  }



  function fullCalendarYearsBetween(from: Date, to: Date): number {

    let years = to.getFullYear() - from.getFullYear()

    const mo = to.getMonth() - from.getMonth()

    if (mo < 0 || (mo === 0 && to.getDate() < from.getDate())) years -= 1

    return Math.max(0, years)

  }



  function ageToday(geburtsdatum: string | null): string {

    const birth = parseIsoDateOnly(geburtsdatum)

    if (!birth) return ''

    const n = fullCalendarYearsBetween(birth, startOfTodayLocal())

    return String(n)

  }



  function memberYearsRoundedDown(eintrittsdatum: string | null): string {

    const joined = parseIsoDateOnly(eintrittsdatum)

    if (!joined) return ''

    const n = fullCalendarYearsBetween(joined, startOfTodayLocal())

    return String(n)

  }



  const ALL_DETAIL_KEYS: (keyof NetxpMember)[] = [

    'id',

    'netxp_id',

    'is_active',

    'first_seen_at',

    'last_seen_at',

    'inactive_since',

    'mitgliedsnummer',

    'vorname',

    'nachname',

    'geburtsdatum',

    'eintrittsdatum',

    'austrittsdatum',

    'mitgliedsart',

    'csv_status',

    'strasse',

    'plz',

    'ort',

    'telefon_privat',

    'telefon_arbeit',

    'email_privat',

    'nx_ssp_registration_code',

    'beitragsnamen',

    'info'

  ]



  /** CSV `Status` column (typed `csv_status`), with fallback to netxp_raw if API omits the field. */
  function netxpCsvStatusText(member: NetxpMember): string {
    const t = member.csv_status
    if (t != null && String(t).trim() !== '') return String(t)
    const raw = member.netxp_raw
    if (!raw || typeof raw !== 'object') return ''
    const alt = raw['Status'] ?? raw['STATUS'] ?? raw['status']
    if (alt == null || alt === '') return ''
    return String(alt)
  }

  function formatDetailValue(member: NetxpMember, key: keyof NetxpMember): string {

    if (key === 'csv_status') {
      const s = netxpCsvStatusText(member)
      return s || m.common_em_dash()
    }

    const v = member[key]

    if (v === null || v === undefined) return m.common_em_dash()

    if (typeof v === 'boolean') return v ? m.common_yes() : m.common_no()

    if (v === '') return m.common_em_dash()

    if (key === 'geburtsdatum' || key === 'eintrittsdatum' || key === 'austrittsdatum') {

      return dateShort(String(v)) || m.common_em_dash()

    }

    return String(v)

  }



  function formatNetxpRawJson(raw: Record<string, unknown> | undefined): string {

    const o = raw && typeof raw === 'object' ? raw : {}

    try {

      return JSON.stringify(o, null, 2)

    } catch {

      return String(o)

    }

  }



  function cellValue(member: NetxpMember, id: ColId): string {

    switch (id) {

      case 'active':

        return member.is_active ? m.common_yes() : m.common_no()

      case 'age':

        return ageToday(member.geburtsdatum)

      case 'member_years':

        return memberYearsRoundedDown(member.eintrittsdatum)

      case 'geburtsdatum':

      case 'eintrittsdatum':

      case 'austrittsdatum':

      case 'first_seen_at':

      case 'last_seen_at':

      case 'inactive_since':

        return dateShort(member[id])

      case 'csv_status':

        return netxpCsvStatusText(member)

      default: {

        const v = member[id as keyof NetxpMember]

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



  let selectedMember = $state<NetxpMember | null>(null)

  let exportLoading = $state(false)



  $effect(() => {

    const items = $netxpMembersItems

    const sel = selectedMember

    if (sel && !items.some((row) => row.id === sel.id)) {

      selectedMember = null

    }

  })



  onDestroy(() => {

    syncAbort?.abort()

  })



  async function runFetch() {

    const t = get(token)

    if (!t) return

    await fetchNetxpMembers(t)

  }



  function netxpExportParams() {

    return {

      activeOnly: get(netxpMembersActiveOnly),

      search: get(netxpMembersSearch),

      currentMembersOnly: get(netxpMembersCurrentOnly),

      youthOnly: get(netxpMembersYouthOnly) === true,

      csvStatusAktiv: get(netxpMembersCsvStatusAktiv) === true,

      csvStatusPassiv: get(netxpMembersCsvStatusPassiv) === true,

      columns: orderedVisibleCols.map((c) => c.id),

      sortBy: get(netxpMembersSortBy),

      sortDir: get(netxpMembersSortDir)

    }

  }



  async function exportCsv() {

    const t = get(token)

    if (!t) return

    exportLoading = true

    try {

      const blob = await exportNetxpMembersCsv(t, netxpExportParams())

      const url = URL.createObjectURL(blob)

      const a = document.createElement('a')

      a.href = url

      a.download = 'netxp-members.csv'

      a.click()

      URL.revokeObjectURL(url)

    } catch {

      /* surface via alert optional */

    } finally {

      exportLoading = false

    }

  }



  async function exportXlsx() {

    const t = get(token)

    if (!t) return

    exportLoading = true

    try {

      const blob = await exportNetxpMembersXlsx(t, netxpExportParams())

      const url = URL.createObjectURL(blob)

      const a = document.createElement('a')

      a.href = url

      a.download = 'netxp-members.xlsx'

      a.click()

      URL.revokeObjectURL(url)

    } catch {

      /* surface via alert optional */

    } finally {

      exportLoading = false

    }

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

      syncError = translateClientErrorMessage(

        e instanceof Error ? e.message : m.netxp_sync_failed_generic()

      )

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



  async function onYouthQuickFilter(youthOnly: boolean) {

    const t = get(token)

    if (!t) return

    netxpMembersPage.set(1)

    await fetchNetxpMembers(t, undefined, { youthOnly })

  }



  async function doPrev() {

    netxpMembersPage.set($netxpMembersPage - 1)

    await runFetch()

  }



  async function doNext() {

    netxpMembersPage.set($netxpMembersPage + 1)

    await runFetch()

  }



  async function onPageSizeChange(e: Event) {

    const t = get(token)

    if (!t) return

    const raw = (e.currentTarget as HTMLSelectElement).value

    persistNetxpMembersPageSize(Number(raw))

    netxpMembersPage.set(1)

    await fetchNetxpMembers(t)

  }

</script>



{#if !$authReady}

  <section class={commonStyles.card}>

    <p class={commonStyles.muted}>{m.common_loading()}</p>

  </section>

{:else if $me?.role !== 'admin'}

  <section class={commonStyles.card}>

    <h2>{m.admin_only_title()}</h2>

    <p class={commonStyles.muted}>{m.admin_only_body()}</p>

    <div class={commonStyles.row}>

      <Link class={commonStyles.btnSecondary} to="/">{m.common_back_to_index()}</Link>

    </div>

  </section>

{:else}

  <section class={commonStyles.card}>

    <div class={pageStyles.pageHeadRow}>

      <h2 class={pageStyles.pageTitle}>{m.netxp_page_title()}</h2>

      <button

        type="button"

        class={pageStyles.syncNetxpButton}

        disabled={syncLoading || $netxpMembersLoading}

        onclick={startNetxpSync}

      >

        {syncLoading ? m.netxp_sync_button_loading() : m.netxp_sync_button()}

      </button>

    </div>



    <NetxpMembersFilters onSearch={doSearch} onRefresh={runFetch} onYouthChange={onYouthQuickFilter} />



    {#if syncError}

      <p class={`${commonStyles.message} ${commonStyles.error}`}>

        {translateClientErrorMessage(syncError)}

      </p>

    {/if}



    {#if syncStatus}

      <p class={commonStyles.muted}>

        {m.netxp_sync_label()}

        {netxpSyncStatusLabel(syncStatus)}{syncRunId ? ` (${syncRunId})` : ''}

      </p>

    {/if}



    {#if syncStatus === 'success' || syncStatus === 'failed' || syncStatus === 'dry_run'}

      <p class={commonStyles.muted}>

        {m.netxp_sync_counts({

          inserted: syncCounts.inserted,

          updated: syncCounts.updated,

          unchanged: syncCounts.unchanged,

          inactivated: syncCounts.inactivated,

          errors: syncCounts.error

        })}

      </p>

      {#if syncNotes}

        <p class={commonStyles.muted}>{syncNotes}</p>

      {/if}

    {/if}



    {#if $netxpMembersError}

      <p class={`${commonStyles.message} ${commonStyles.error}`}>

        {translateClientErrorMessage($netxpMembersError)}

      </p>

    {/if}



    <ColumnPicker

      columns={COL_DEFS.map((c) => ({ id: c.id, label: netxpColumnLabel(c.id) }))}

      bind:visibleIds={visibleColIds}

      summaryHint={m.netxp_column_picker_hint()}

      onReset={resetColumnsToDefault}

    />



    {#if $netxpMembersLoading}

      <p class={commonStyles.muted}>{m.netxp_table_loading()}</p>

    {/if}



    {#if !$netxpMembersLoading && $netxpMembersItems.length > 0}

      {#key `${$netxpMembersSortBy ?? ''}-${$netxpMembersSortDir}-${$netxpMembersPage}`}

        <DataTable

          columns={tableColumns}

          rows={$netxpMembersItems}

          sortBy={$netxpMembersSortBy}

          sortDir={$netxpMembersSortDir}

          onSort={(id) => sortByColumn(id as ColId)}

          getCell={(row, colId) => cellValue(row as NetxpMember, colId as ColId)}

          getRowKey={(row) => (row as NetxpMember).id}

          onRowClick={(row) => (selectedMember = row as NetxpMember)}

          selectedKey={selectedMember?.id ?? null}

        />

      {/key}

      {#if $netxpMembersSortBy === 'csv_status'}

        <p class={commonStyles.muted}>{m.netxp_sort_csv_status_hint()}</p>

      {/if}



      {#if selectedMember}

        <div

          class={pageStyles.detailPanel}

          role="region"

          aria-label={m.netxp_detail_aria()}

        >

          <div class={pageStyles.detailPanelHeader}>

            <h3 class={pageStyles.detailPanelTitle}>{m.netxp_detail_title()}</h3>

            <button

              type="button"

              class={commonStyles.btnSecondary}

              onclick={() => (selectedMember = null)}

            >

              {m.netxp_detail_close()}

            </button>

          </div>

          <p class={pageStyles.detailPanelSubtitle}>

            {[selectedMember.vorname, selectedMember.nachname].filter(Boolean).join(' ') ||

              selectedMember.netxp_id}

          </p>

          <dl class={pageStyles.detailGrid}>

            {#each ALL_DETAIL_KEYS as key}

              <dt>{netxpDetailLabel(key)}</dt>

              <dd>{formatDetailValue(selectedMember, key)}</dd>

            {/each}

            <dt>{m.netxp_detail_age_today()}</dt>

            <dd>{ageToday(selectedMember.geburtsdatum) || m.common_em_dash()}</dd>

            <dt>{m.netxp_detail_member_years()}</dt>

            <dd>{memberYearsRoundedDown(selectedMember.eintrittsdatum) || m.common_em_dash()}</dd>

            <dt>{m.netxp_detail_netxp_raw()}</dt>

            <dd class={pageStyles.detailRawCell}>

              <pre class={pageStyles.detailRaw}>{formatNetxpRawJson(selectedMember.netxp_raw)}</pre>

            </dd>

          </dl>

        </div>

      {/if}



      <div class={pageStyles.paginationBar}>

        <div class={pageStyles.paginationNav}>

          <button

            class={commonStyles.btnSecondary}

            disabled={$netxpMembersLoading || $netxpMembersPage <= 1}

            onclick={doPrev}

          >

            {m.netxp_pagination_prev()}

          </button>

          <button

            class={commonStyles.btnSecondary}

            disabled={$netxpMembersLoading || $netxpMembersPage >= netxpMembersTotalPagesValue}

            onclick={doNext}

          >

            {m.netxp_pagination_next()}

          </button>

        </div>



        <p class={`${commonStyles.muted} ${pageStyles.paginationMeta}`}>

          {m.netxp_pagination_meta({

            page: $netxpMembersPage,

            totalPages: netxpMembersTotalPagesValue,

            total: $netxpMembersTotal

          })}

        </p>



        <div class={pageStyles.paginationPageSize}>

          <PageSizeSelect

            options={NETXP_PAGE_SIZE_OPTIONS}

            value={$netxpMembersPageSize}

            disabled={$netxpMembersLoading}

            onChange={onPageSizeChange}

          />

        </div>

      </div>

    {:else if !$netxpMembersLoading && !$netxpMembersError}

      <p class={commonStyles.muted}>{m.netxp_table_no_results()}</p>

    {/if}



    {#if !$netxpMembersLoading && !$netxpMembersError}

      <div class={pageStyles.exportRow}>

        <button

          class={commonStyles.btnSecondary}

          disabled={exportLoading || $netxpMembersLoading}

          onclick={exportCsv}

        >

          {exportLoading ? m.netxp_export_csv_loading() : m.netxp_export_csv()}

        </button>

        <button

          class={commonStyles.btnSecondary}

          disabled={exportLoading || $netxpMembersLoading}

          onclick={exportXlsx}

        >

          {exportLoading ? m.netxp_export_xlsx_loading() : m.netxp_export_xlsx()}

        </button>

      </div>

    {/if}

  </section>

{/if}



