<script lang="ts">
  import { Link } from 'svelte-navigator'
  import { apiStatus, login, logout, me } from '../stores/auth'
  import commonStyles from '../styles/common.module.scss'

  // Login form state
  let loginEmail = $state('')
  let loginPassword = $state('')
  let loginError = $state<string | null>(null)
  let loading = $state(false)

  async function doLogin() {
    loading = true
    loginError = null

    try {
      await login(loginEmail, loginPassword)
      // Redirect is handled centrally by App via `redirectToIndex`.
    } catch (e) {
      loginError = e instanceof Error ? e.message : 'Network error'
    } finally {
      loading = false
    }
  }
</script>

{#if $me}
  <section class={commonStyles.card}>
    <h2>Already signed in</h2>
    <p class={commonStyles.muted}>
      You are logged in as <b>{$me.email}</b> (<b>{$me.role}</b>).
    </p>
    <div class={commonStyles.row}>
      <button class={commonStyles.btnSecondary} onclick={logout}>Logout</button>
      <Link class={commonStyles.btnSecondary} to="/">Back to Index</Link>
    </div>
  </section>
{:else}
  <section class={commonStyles.card}>
    <h2>Login</h2>

    <label>
      Email
      <input bind:value={loginEmail} type="email" autocomplete="email" />
    </label>

    <label>
      Password
      <input bind:value={loginPassword} type="password" autocomplete="current-password" />
    </label>

    <div class={commonStyles.row}>
      <button
        class={commonStyles.btnPrimary}
        disabled={loading || $apiStatus.includes('offline')}
        onclick={doLogin}
      >
        Sign in
      </button>
    </div>

    {#if loginError}
      <p class={`${commonStyles.message} ${commonStyles.error}`}>{loginError}</p>
    {/if}
  </section>
{/if}

