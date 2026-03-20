<script lang="ts">
  import { onDestroy, onMount } from 'svelte'
  import { Link, useNavigate } from 'svelte-navigator'
  import { apiStatus, logout, me, redirectToIndex } from '../stores/auth'
  import commonStyles from '../styles/common.module.scss'

  const navigate = useNavigate()

  // Centralized redirect after auth actions.
  // This lives in `Layout` so `useNavigate()` runs inside a Router context.
  let lastRedirect = 0
  $: {
    const v = $redirectToIndex
    if (v > lastRedirect) {
      lastRedirect = v
      navigate('/')
    }
  }

  let mobileMenuOpen = false
  let adminOpenDesktop = false
  let adminOpenMobile = false

  let adminDropdownEl: HTMLElement | null = null

  function closeMenus() {
    mobileMenuOpen = false
    adminOpenDesktop = false
    adminOpenMobile = false
  }

  function onDocumentClick(e: MouseEvent) {
    if (!adminDropdownEl) return
    const target = e.target as Node | null
    if (!target) return
    if (!adminDropdownEl.contains(target)) {
      adminOpenDesktop = false
    }
  }

  onMount(() => {
    document.addEventListener('click', onDocumentClick)
  })

  onDestroy(() => {
    document.removeEventListener('click', onDocumentClick)
  })
</script>

<header class={commonStyles.header}>
  <div class={commonStyles.headerInner}>
    <Link class={commonStyles.brand} to="/">Treptower Teufel</Link>

    <nav class={commonStyles.desktopNav} aria-label="Main navigation">
      <Link class={commonStyles.navItem} to="/" onclick={() => closeMenus()}>Index</Link>

      {#if !$me}
        <Link class={commonStyles.navItem} to="/login" onclick={() => closeMenus()}>Login</Link>
      {/if}

      {#if $me?.role === 'admin'}
        <div class={commonStyles.navDropdown} bind:this={adminDropdownEl}>
          <button
            class={commonStyles.navItemButton}
            type="button"
            aria-haspopup="menu"
            aria-expanded={adminOpenDesktop}
            onclick={(e) => {
              e.stopPropagation()
              adminOpenDesktop = !adminOpenDesktop
            }}
          >
            Admin
          </button>

          {#if adminOpenDesktop}
            <div class={commonStyles.dropdownMenu} role="menu" aria-label="Admin menu">
              <Link
                class={commonStyles.dropdownItem}
                to="/admin/create-user"
                onclick={() => {
                  adminOpenDesktop = false
                }}
              >
                Create user
              </Link>
              <Link
                class={commonStyles.dropdownItem}
                to="/admin/netxp-members"
                onclick={() => {
                  adminOpenDesktop = false
                }}
              >
                NetXP members
              </Link>
            </div>
          {/if}
        </div>
      {/if}
    </nav>

    <div class={commonStyles.headerRight}>
      {#if $me}
        <div class={commonStyles.userInfo}>
          Logged in as <b>{$me.email}</b> (<b>{$me.role}</b>)
        </div>
        <button class={commonStyles.logoutBtn} type="button" onclick={logout}>Logout</button>
      {/if}

      <button
        class={commonStyles.hamburger}
        type="button"
        aria-label="Open menu"
        aria-expanded={mobileMenuOpen}
        onclick={() => {
          mobileMenuOpen = !mobileMenuOpen
          // Keep admin dropdown state in sync when opening/closing the drawer.
          if (!mobileMenuOpen) adminOpenMobile = false
        }}
      >
        <span aria-hidden="true">&#9776;</span>
      </button>
    </div>
  </div>

  {#if mobileMenuOpen}
    <div class={commonStyles.mobileMenu}>
      <div class={commonStyles.mobileMenuPanel}>
        <div class={commonStyles.mobileNav}>
          <Link class={commonStyles.mobileNavItem} to="/" onclick={() => closeMenus()}>Index</Link>

          {#if !$me}
            <Link class={commonStyles.mobileNavItem} to="/login" onclick={() => closeMenus()}>Login</Link>
          {/if}

          {#if $me?.role === 'admin'}
            <div class={commonStyles.mobileAdminDropdown}>
              <button
                class={commonStyles.mobileNavItemButton}
                type="button"
                aria-haspopup="menu"
                aria-expanded={adminOpenMobile}
                onclick={() => (adminOpenMobile = !adminOpenMobile)}
              >
                Admin
              </button>

              {#if adminOpenMobile}
                <div class={commonStyles.mobileAdminItems} role="menu" aria-label="Admin menu">
                  <Link
                    class={commonStyles.mobileNavItem}
                    to="/admin/create-user"
                    onclick={() => {
                      adminOpenMobile = false
                      mobileMenuOpen = false
                    }}
                  >
                    Create user
                  </Link>
                  <Link
                    class={commonStyles.mobileNavItem}
                    to="/admin/netxp-members"
                    onclick={() => {
                      adminOpenMobile = false
                      mobileMenuOpen = false
                    }}
                  >
                    NetXP members
                  </Link>
                </div>
              {/if}
            </div>
          {/if}
        </div>

        {#if $me}
          <p class={commonStyles.mobileUserInfo}>
            Logged in as <b>{$me.email}</b> (<b>{$me.role}</b>)
          </p>
          <div class={commonStyles.row}>
            <button class={commonStyles.btnSecondary} type="button" onclick={logout}>Logout</button>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</header>

<main class={commonStyles.content}>
  <p class={commonStyles.apiStatus}>{$apiStatus}</p>
  <slot />
</main>

