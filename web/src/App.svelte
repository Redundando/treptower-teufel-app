<script lang="ts">
  import { onMount } from 'svelte'
  import { Route, Router } from 'svelte-navigator'
  import Layout from './layout/Layout.svelte'
  import IndexPage from './routes/IndexPage.svelte'
  import LoginPage from './routes/LoginPage.svelte'
  import AdminCreateUserPage from './routes/AdminCreateUserPage.svelte'
  import AdminNetxpMembersPage from './routes/admin/netxp-members/AdminNetxpMembersPage.svelte'
  import MembershipStatsPage from './routes/MembershipStatsPage.svelte'
  import { bootstrapAuth } from './stores/auth'

  onMount(() => {
    void bootstrapAuth()
  })
</script>

<Router>
  <Layout>
    <Route path="/" component={IndexPage} />
    <Route path="/login" component={LoginPage} />
    <Route path="/membership-stats" primary={false} component={MembershipStatsPage} />
    <Route path="/admin/create-user" primary={false} component={AdminCreateUserPage} />
    <Route path="/admin/netxp-members" primary={false} component={AdminNetxpMembersPage} />
    <Route path="*" component={IndexPage} />
  </Layout>
</Router>

