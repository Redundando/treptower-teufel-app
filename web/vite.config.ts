import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

export default defineConfig({
  plugins: [svelte()],
  optimizeDeps: { exclude: ['svelte-navigator'] },
  server: {
    port: 5173,
    proxy: {
      // API: change port if you run uvicorn on 8001 etc.
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  preview: {
    port: 5173,
    host: '0.0.0.0',
    allowedHosts: ['staging-app.treptower-teufel.de', 'localhost', '127.0.0.1'],
  },
})
