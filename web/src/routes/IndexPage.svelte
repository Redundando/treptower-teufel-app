<script lang="ts">
  import { Link } from 'svelte-navigator'
  import { me } from '../stores/auth'
  import commonStyles from '../styles/common.module.scss'
  import * as m from '../paraglide/messages.js'
</script>

<section class={commonStyles.card}>
  <h2>{m.index_title()}</h2>

  <ul class={commonStyles.toolList}>
    <li>
      <Link to="/login"
        >{m.index_login_link()}{#if $me} {m.index_login_signed_in_suffix()}{/if}</Link
      >
    </li>

    {#if $me?.role === 'admin'}
      <li>
        <Link to="/admin/create-user">{m.index_admin_create()}</Link>
      </li>
      <li>
        <Link to="/admin/netxp-members">{m.index_admin_netxp()}</Link>
      </li>
    {:else if $me}
      <li class={commonStyles.muted}>{m.index_no_tools()}</li>
    {/if}
  </ul>
</section>
