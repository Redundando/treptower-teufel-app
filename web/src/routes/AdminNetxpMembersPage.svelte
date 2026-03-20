<script lang="ts">
  import { Link } from 'svelte-navigator'
  import { authReady, me, token } from '../stores/auth'
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

  async function runFetch() {
    const t = get(token)
    if (!t) return
    await fetchMembers(t)
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

