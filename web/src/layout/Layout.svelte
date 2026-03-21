<script lang="ts">
  import { onDestroy, onMount } from 'svelte'
  import { Link, useNavigate } from 'svelte-navigator'
  import { logout, me, redirectToIndex } from '../stores/auth'
  import type { Role } from '../types/auth'
  import commonStyles from '../styles/common.module.scss'
  import { locales, getLocale, setLocale, toLocale } from '../paraglide/runtime.js'
  import * as msg from '../paraglide/messages.js'
  import { emailLocalPart } from '../lib/userDisplay'

  const navigate = useNavigate()

  function loggedInFullLabel(email: string, role: Role) {
    return msg.layout_logged_in_as({ email, role })
  }

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
  let localeDropdownEl: HTMLElement | null = null

  let localeOpenDesktop = false
  let localeOpenMobile = false

  function closeMenus() {
    mobileMenuOpen = false
    adminOpenDesktop = false
    adminOpenMobile = false
    localeOpenDesktop = false
    localeOpenMobile = false
  }

  function onDocumentClick(e: MouseEvent) {
    const target = e.target as Node | null
    if (!target) return
    if (adminDropdownEl && !adminDropdownEl.contains(target)) {
      adminOpenDesktop = false
    }
    if (localeDropdownEl && !localeDropdownEl.contains(target)) {
      localeOpenDesktop = false
    }
  }

  function pickLocale(raw: string) {
    const next = toLocale(raw)
    if (!next || next === getLocale()) {
      localeOpenDesktop = false
      localeOpenMobile = false
      return
    }
    closeMenus()
    setLocale(next)
  }

  function localeLabel(code: string): string {
    return code === 'de' ? msg.lang_de() : msg.lang_en()
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

    <nav class={commonStyles.desktopNav} aria-label={msg.nav_main()}>
      <Link class={commonStyles.navItem} to="/" onclick={() => closeMenus()}>{msg.nav_index()}</Link>
      <Link class={commonStyles.navItem} to="/membership-stats" onclick={() => closeMenus()}
        >{msg.nav_membership_stats()}</Link
      >

      {#if !$me}
        <Link class={commonStyles.navItem} to="/login" onclick={() => closeMenus()}>{msg.nav_login()}</Link>
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
              localeOpenDesktop = false
              adminOpenDesktop = !adminOpenDesktop
            }}
          >
            {msg.nav_admin()}
          </button>

          {#if adminOpenDesktop}
            <div class={commonStyles.dropdownMenu} role="menu" aria-label={msg.nav_admin_menu()}>
              <Link
                class={commonStyles.dropdownItem}
                to="/admin/create-user"
                onclick={() => {
                  adminOpenDesktop = false
                }}
              >
                {msg.nav_create_user()}
              </Link>
              <Link
                class={commonStyles.dropdownItem}
                to="/admin/netxp-members"
                onclick={() => {
                  adminOpenDesktop = false
                }}
              >
                {msg.nav_netxp_members()}
              </Link>
            </div>
          {/if}
        </div>
      {/if}
    </nav>

    <div class={commonStyles.headerRight}>
      <div class={commonStyles.localeDropdown} bind:this={localeDropdownEl}>
        <button
          type="button"
          class={commonStyles.localeMenuButton}
          aria-label={msg.nav_language()}
          aria-haspopup="listbox"
          aria-expanded={localeOpenDesktop}
          onclick={(e) => {
            e.stopPropagation()
            adminOpenDesktop = false
            localeOpenDesktop = !localeOpenDesktop
          }}
        >
          <span class={commonStyles.localeMenuButtonLabel}>{localeLabel(getLocale())}</span>
          <svg
            class={commonStyles.localeChevron}
            width="18"
            height="18"
            viewBox="0 0 24 24"
            aria-hidden="true"
            fill="none"
            stroke="currentColor"
            stroke-width="2.2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M6 9l6 6 6-6" />
          </svg>
        </button>
        {#if localeOpenDesktop}
          <div class={commonStyles.localeDropdownMenu} role="listbox" aria-label={msg.nav_language()}>
            {#each locales as loc}
              <button
                type="button"
                role="option"
                class={`${commonStyles.localeMenuOption} ${getLocale() === loc ? commonStyles.localeMenuOptionSelected : ''}`.trim()}
                aria-selected={getLocale() === loc}
                onclick={(e) => {
                  e.stopPropagation()
                  pickLocale(loc)
                }}
              >
                {localeLabel(loc)}
              </button>
            {/each}
          </div>
        {/if}
      </div>

      {#if $me}
        <div
          class={commonStyles.userInfo}
          title={loggedInFullLabel($me.email, $me.role)}
          aria-label={loggedInFullLabel($me.email, $me.role)}
        >
          <span aria-hidden="true" class={commonStyles.userInfoVisual}>
            <span class={commonStyles.userInfoEmail}>{emailLocalPart($me.email)}</span>
            <span class={commonStyles.userInfoSep}>·</span>
            <span class={commonStyles.userInfoRole}>
              {$me.role === 'admin' ? msg.role_option_admin() : msg.role_option_member()}
            </span>
          </span>
        </div>
        <button class={commonStyles.logoutBtn} type="button" onclick={logout}>{msg.layout_logout()}</button>
      {/if}

      <button
        class={commonStyles.hamburger}
        type="button"
        aria-label={msg.nav_open_menu()}
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
          <div class={commonStyles.mobileLocaleBlock}>
            <button
              type="button"
              class={commonStyles.mobileLocaleToggle}
              aria-expanded={localeOpenMobile}
              aria-haspopup="listbox"
              onclick={() => (localeOpenMobile = !localeOpenMobile)}
            >
              <span>{msg.nav_language()}: {localeLabel(getLocale())}</span>
              <svg
                class={commonStyles.localeChevron}
                width="18"
                height="18"
                viewBox="0 0 24 24"
                aria-hidden="true"
                fill="none"
                stroke="currentColor"
                stroke-width="2.2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M6 9l6 6 6-6" />
              </svg>
            </button>
            {#if localeOpenMobile}
              <div class={commonStyles.mobileLocaleMenu} role="listbox">
                {#each locales as loc}
                  <button
                    type="button"
                    role="option"
                    class={`${commonStyles.mobileLocaleOption} ${getLocale() === loc ? commonStyles.mobileLocaleOptionSelected : ''}`.trim()}
                    aria-selected={getLocale() === loc}
                    onclick={() => pickLocale(loc)}
                  >
                    {localeLabel(loc)}
                  </button>
                {/each}
              </div>
            {/if}
          </div>

          <Link class={commonStyles.mobileNavItem} to="/" onclick={() => closeMenus()}>{msg.nav_index()}</Link>
          <Link
            class={commonStyles.mobileNavItem}
            to="/membership-stats"
            onclick={() => closeMenus()}
          >
            {msg.nav_membership_stats()}
          </Link>

          {#if !$me}
            <Link class={commonStyles.mobileNavItem} to="/login" onclick={() => closeMenus()}>{msg.nav_login()}</Link>
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
                {msg.nav_admin()}
              </button>

              {#if adminOpenMobile}
                <div class={commonStyles.mobileAdminItems} role="menu" aria-label={msg.nav_admin_menu()}>
                  <Link
                    class={commonStyles.mobileNavItem}
                    to="/admin/create-user"
                    onclick={() => {
                      adminOpenMobile = false
                      mobileMenuOpen = false
                    }}
                  >
                    {msg.nav_create_user()}
                  </Link>
                  <Link
                    class={commonStyles.mobileNavItem}
                    to="/admin/netxp-members"
                    onclick={() => {
                      adminOpenMobile = false
                      mobileMenuOpen = false
                    }}
                  >
                    {msg.nav_netxp_members()}
                  </Link>
                </div>
              {/if}
            </div>
          {/if}
        </div>

        {#if $me}
          <p
            class={commonStyles.mobileUserInfo}
            title={loggedInFullLabel($me.email, $me.role)}
            aria-label={loggedInFullLabel($me.email, $me.role)}
          >
            <span aria-hidden="true" class={commonStyles.mobileUserInfoVisual}>
              <span class={commonStyles.userInfoEmail}>{emailLocalPart($me.email)}</span>
              <span class={commonStyles.userInfoSep}>·</span>
              <span class={commonStyles.userInfoRole}>
                {$me.role === 'admin' ? msg.role_option_admin() : msg.role_option_member()}
              </span>
            </span>
          </p>
          <div class={commonStyles.row}>
            <button class={commonStyles.btnSecondary} type="button" onclick={logout}>{msg.layout_logout()}</button>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</header>

<main class={commonStyles.content}>
  <slot />
</main>
