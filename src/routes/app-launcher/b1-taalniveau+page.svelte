<script>
  import NavBar from '$lib/components/layout/NavBar.svelte';
  import Sidebar from '$lib/components/layout/Sidebar.svelte';
  import B1Tool from '$lib/components/app-launcher/b1-taalniveau/b1-logic.svelte';

  // Stores
  import { showSidebar } from '$lib/stores';
  
  // Dummy functies voor NavBar props
  function initNewChat() {}
  const chat = { id: null };
</script>

<div class="flex h-screen bg-gray-100 dark:bg-gray-900">
  <!-- Sidebar -->
  <Sidebar />

  <!-- Hoofdinhoud -->
  <div class="flex-1 flex flex-col">
    <!-- NavBar met vereiste props -->
    <NavBar {initNewChat} {chat} />

    <!-- Inhoud van de B1-Taalniveau-app -->
    <main class="flex-1 p-6 overflow-y-auto">
      <div class="max-w-4xl mx-auto">
        <div class="mb-6">
          <h1 class="text-3xl font-bold text-gray-800 dark:text-white">B1-Taalniveau Vertaler</h1>
          <p class="text-gray-600 dark:text-gray-300 mt-2">
            Deze tool helpt je om teksten te vereenvoudigen naar B1-taalniveau, zodat ze begrijpelijk zijn voor een breder publiek.
          </p>
        </div>
        
        <B1Tool />
      </div>
    </main>
  </div>
</div>
