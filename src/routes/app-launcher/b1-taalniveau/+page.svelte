<script>
  import NavBar from '$lib/components/layout/NavBar.svelte';
  import Sidebar from '$lib/components/layout/Sidebar.svelte';
  import B1Tool from '$lib/components/app-launcher/b1-taalniveau/b1-logic.svelte';

  // Stores (indien nodig)
  import { showSidebar } from '$lib/stores';
</script>

<div class="flex h-screen bg-gray-100 dark:bg-gray-900">
  <!-- Sidebar -->
  <Sidebar />

  <!-- Hoofdinhoud -->
  <div class="flex-1 flex flex-col">
    <!-- NavBar -->
    <NavBar />

    <!-- Inhoud van de B1-Taalniveau-app -->
    <main class="flex-1 p-6">
      <B1Tool />
    </main>
  </div>
</div>

<style>
  main {
    overflow-y: auto;
  }
</style>