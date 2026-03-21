<script lang="ts">
  import { Link } from 'svelte-navigator'
  import { login, logout, me } from '../stores/auth'
  import commonStyles from '../styles/common.module.scss'
  import * as m from '../paraglide/messages.js'
  import { translateClientErrorMessage } from '../lib/apiErrorMessage'

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
      loginError = translateClientErrorMessage(e instanceof Error ? e.message : m.api_err_network())
    } finally {
      loading = false
    }
  }
</script>

{#if $me}
  <section class={commonStyles.card}>
    <h2>{m.login_already_signed_in_title()}</h2>
    <p class={commonStyles.muted}>
      {m.login_already_signed_in_body({ email: $me.email, role: $me.role })}
    </p>
    <div class={commonStyles.row}>
      <button class={commonStyles.btnSecondary} onclick={logout}>{m.layout_logout()}</button>
      <Link class={commonStyles.btnSecondary} to="/">{m.common_back_to_index()}</Link>
    </div>
  </section>
{:else}
  <section class={commonStyles.card}>
    <h2>{m.login_title()}</h2>

    <label>
      {m.login_email()}
      <input bind:value={loginEmail} type="email" autocomplete="email" />
    </label>

    <label>
      {m.login_password()}
      <input bind:value={loginPassword} type="password" autocomplete="current-password" />
    </label>

    <div class={commonStyles.row}>
      <button
        class={commonStyles.btnPrimary}
        disabled={loading}
        onclick={doLogin}
      >
        {m.login_sign_in()}
      </button>
    </div>

    {#if loginError}
      <p class={`${commonStyles.message} ${commonStyles.error}`}>{loginError}</p>
    {/if}
  </section>
{/if}
