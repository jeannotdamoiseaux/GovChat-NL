<script>
    import Sidebar from '$lib/components/layout/Sidebar.svelte';
    import AppGrid from '$lib/components/app-launcher/AppGrid.svelte';
    import NavBar from '$lib/components/layout/NavBar.svelte';
    
    // Stores
    import { showSidebar, models, user } from '$lib/stores';
    
    // Model selectie - dit wordt gedeeld met NavBar
    let selectedModels = [''];
    
    // Als er geen model is geselecteerd, selecteer dan het eerste beschikbare model
    $: if (selectedModels.length === 0 || (selectedModels.length === 1 && selectedModels[0] === '') && $models?.length > 0) {
        selectedModels = [$models[0].id];
    }
</script>

<div class="flex h-screen overflow-hidden bg-gray-100 dark:bg-gray-900">
    <!-- Sidebar -->
    <Sidebar />
    
    <!-- Hoofdinhoud -->
    <div class="flex-1 flex flex-col">
        <!-- NavBar - bind selectedModels om de model selector te gebruiken -->
        <NavBar bind:selectedModels />
        
        <!-- Main Content -->
        <main class="flex-1 p-6 overflow-y-auto">
            <h1 class="text-3xl font-bold text-gray-800 dark:text-gray-200 mb-6">
                App Launcher
            </h1>
            <AppGrid />
        </main>
    </div>
</div>

<style>
    /* Algemene layout */
    html, body, div, main {
        margin: 0;
        padding: 0;
        height: 100%;
    }

    main {
        overflow-y: auto;
    }
</style>
