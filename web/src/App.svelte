<script lang="ts">
  import { onMount } from 'svelte'
  import { Route, Router } from 'svelte-navigator'
  import Layout from './layout/Layout.svelte'
  import IndexPage from './routes/IndexPage.svelte'
  import LoginPage from './routes/LoginPage.svelte'
  import AdminCreateUserPage from './routes/AdminCreateUserPage.svelte'
  import AdminNetxpMembersPage from './routes/AdminNetxpMembersPage.svelte'
  import { bootstrapAuth } from './stores/auth'

  onMount(() => {
    void bootstrapAuth()
  })
</script>

<Router>
  <Layout>
    <Route path="/" component={IndexPage} />
    <Route path="/login" component={LoginPage} />
    <Route path="/admin/create-user" component={AdminCreateUserPage} />
    <Route path="/admin/netxp-members" component={AdminNetxpMembersPage} />
    <Route path="*" component={IndexPage} />
  </Layout>
</Router>

