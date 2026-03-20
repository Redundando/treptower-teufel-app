/// <reference types="vite/client" />
declare module '*.svelte' {
  import type { Component } from 'svelte'
  const component: Component
  export default component
}

declare module '*.scss' {
  const css: string
  export default css
}

declare module '*.module.scss' {
  const classes: Record<string, string>
  export default classes
}
