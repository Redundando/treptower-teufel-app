<script lang="ts">
  import { Link } from 'svelte-navigator'
  import { me } from '../stores/auth'
  import commonStyles from '../styles/common.module.scss'
</script>

<section class={commonStyles.card}>
  <h2>Index</h2>

  <ul class={commonStyles.toolList}>
    <li>
      <Link to="/login">Login{#if $me} (signed in){/if}</Link>
    </li>

    {#if $me?.role === 'admin'}
      <li>
        <Link to="/admin/create-user">Admin: Create user</Link>
      </li>
      <li>
        <Link to="/admin/netxp-members">Admin: NetXP Members</Link>
      </li>
    {:else if $me}
      <li class={commonStyles.muted}>No tools available for your role.</li>
    {/if}
  </ul>
</section>

