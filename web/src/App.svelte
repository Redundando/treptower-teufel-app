<script lang="ts">
  let apiStatus = $state('…')
  async function checkApi() {
    try {
      const r = await fetch('/api/health')
      const j = await r.json()
      apiStatus = r.ok ? `API: ${j.status}` : `API: ${r.status}`
    } catch (e) {
      apiStatus = 'API: offline'
    }
  }
  checkApi()
</script>

<main>
  <h1>Hello, Treptower Teufel</h1>
  <p>{apiStatus}</p>
</main>

<style>
  main {
    font-family: system-ui, sans-serif;
    max-width: 40ch;
    margin: 4rem auto;
    padding: 0 1rem;
  }
  h1 {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
  }
</style>
