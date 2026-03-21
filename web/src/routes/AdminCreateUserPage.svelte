<script lang="ts">
  import { Link } from 'svelte-navigator'
  import { adminCreateUser, authReady, me } from '../stores/auth'
  import type { Role } from '../types/auth'
  import { DataTable, type DataTableColumnDef } from '../components/data-table'
  import commonStyles from '../styles/common.module.scss'
  import * as m from '../paraglide/messages.js'
  import { translateClientErrorMessage } from '../lib/apiErrorMessage'

  const roleTableCols: DataTableColumnDef[] = [
    { id: 'role', label: m.role_table_col_role(), sortable: false },
    { id: 'description', label: m.role_table_col_access(), sortable: false }
  ]

  let roleTableRows = $derived([
    { role: m.role_option_admin(), description: m.role_admin_desc() },
    { role: m.role_option_member(), description: m.role_member_desc() }
  ])

  let newUserEmail = $state('')
  let newUserPassword = $state('')
  let newUserRole = $state<Role>('member')
  let newUserMessage = $state<string | null>(null)
  let creating = $state(false)

  async function doCreateUser() {
    creating = true
    newUserMessage = null

    try {
      const msg = await adminCreateUser({
        email: newUserEmail,
        password: newUserPassword,
        role: newUserRole
      })
      newUserMessage = msg

      newUserEmail = ''
      newUserPassword = ''
      newUserRole = 'member'
    } catch (e) {
      newUserMessage = translateClientErrorMessage(
        e instanceof Error ? e.message : m.api_err_network()
      )
    } finally {
      creating = false
    }
  }

  function noopSort(_columnId: string) {
    /* static demo table */
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
    <h2>{m.admin_create_title()}</h2>

    <label>
      {m.admin_create_email()}
      <input bind:value={newUserEmail} type="email" autocomplete="email" />
    </label>

    <label>
      {m.admin_create_password()}
      <input
        bind:value={newUserPassword}
        type="password"
        autocomplete="new-password"
      />
    </label>

    <label>
      {m.admin_create_role()}
      <select bind:value={newUserRole}>
        <option value="member">{m.role_option_member()}</option>
        <option value="admin">{m.role_option_admin()}</option>
      </select>
    </label>

    <div class={commonStyles.row}>
      <button class={commonStyles.btnPrimary} disabled={creating} onclick={doCreateUser}
        >{m.admin_create_submit()}</button
      >
    </div>

    {#if newUserMessage}
      <p class={commonStyles.message}>{newUserMessage}</p>
    {/if}

    <h3 class={commonStyles.muted}>{m.admin_create_roles_ref()}</h3>
    <DataTable
      columns={roleTableCols}
      rows={roleTableRows}
      sortBy={null}
      sortDir="asc"
      onSort={noopSort}
      getCell={(row, colId) => String((row as Record<string, string>)[colId] ?? '')}
      getRowKey={(row) => (row as { role: string }).role}
    />
  </section>
{/if}
