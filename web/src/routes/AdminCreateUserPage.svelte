<script lang="ts">
  import { Link } from 'svelte-navigator'
  import { adminCreateUser, authReady, me } from '../stores/auth'
  import type { Role } from '../types/auth'
  import commonStyles from '../styles/common.module.scss'

  // Admin create-user form state
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

      // Preserve current behavior: reset form after successful create.
      newUserEmail = ''
      newUserPassword = ''
      newUserRole = 'member'
    } catch (e) {
      newUserMessage = e instanceof Error ? e.message : 'Network error'
    } finally {
      creating = false
    }
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
    <h2>Admin: Create user</h2>

    <label>
      Email
      <input bind:value={newUserEmail} type="email" autocomplete="email" />
    </label>

    <label>
      Password
      <input
        bind:value={newUserPassword}
        type="password"
        autocomplete="new-password"
      />
    </label>

    <label>
      Role
      <select bind:value={newUserRole}>
        <option value="member">member</option>
        <option value="admin">admin</option>
      </select>
    </label>

    <div class={commonStyles.row}>
      <button class={commonStyles.btnPrimary} disabled={creating} onclick={doCreateUser}>Create</button>
    </div>

    {#if newUserMessage}
      <p class={commonStyles.message}>{newUserMessage}</p>
    {/if}
  </section>
{/if}

