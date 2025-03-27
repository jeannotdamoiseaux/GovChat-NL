<script>
  import NavBar from '$lib/components/layout/NavBar.svelte';
  import Sidebar from '$lib/components/layout/Sidebar.svelte';
  import B1Tool from '$lib/components/app-launcher/b1-taalniveau/b1-logic.svelte';

  // Stores
  import { showSidebar, models } from '$lib/stores';
  
  // Model selectie - dit wordt gedeeld met NavBar
  let selectedModels = [''];
  
  // Als er geen model is geselecteerd, selecteer dan het eerste beschikbare model
  $: if (selectedModels.length === 0 || (selectedModels.length === 1 && selectedModels[0] === '') && $models.length > 0) {
    selectedModels = [$models[0].id];
  }
</script>

<div class="flex h-screen bg-gray-100 dark:bg-gray-900 text-white">
  <!-- Sidebar -->
  <Sidebar />

  <!-- Hoofdinhoud -->
  <div class="flex-1 flex flex-col">
    <!-- NavBar - bind selectedModels om de model selector te gebruiken -->
    <NavBar bind:selectedModels />

    <!-- Inhoud van de B1-Taalniveau-app -->
    <main class="flex-1 p-6 overflow-y-auto text-white">
      <B1Tool {selectedModels} />
    </main>
  </div>
</div>

<style>
  main {
    overflow-y: auto;
  }
</style>
