<script lang="ts">
    import { subsidyStore } from '$lib/stores/subsidyStore';
    import type { SubsidyResponse } from '$lib/stores/subsidyStore';
    import { onMount } from 'svelte';

    // Subscribe aan de geselecteerde output uit de store
    let selectedDataFromPart1: SubsidyResponse | null = null;

    const unsubscribe = subsidyStore.subscribe(store => {
        selectedDataFromPart1 = store.selectedOutput;
    });

    onMount(() => {
        // Optioneel: Log de data wanneer het component mount
        console.log("Data ontvangen van Deel 1:", selectedDataFromPart1);

        // Cleanup de subscription wanneer het component unmount
        return () => unsubscribe();
    });

    // Je kunt nu selectedDataFromPart1 gebruiken in je component logica en template

</script>

<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
    <h2 class="text-2xl font-bold text-gray-800 dark:text-white text-center mb-6">
        Subsidie Analyse - Deel 2
    </h2>

    {#if selectedDataFromPart1}
        <div class="space-y-4">
            <h3 class="text-lg font-semibold text-gray-800 dark:text-white">
                Gebaseerd op: "{selectedDataFromPart1.name}"
            </h3>

            {#if selectedDataFromPart1.summary}
                <div class="border border-gray-300 rounded-md p-3 bg-gray-50 dark:bg-gray-700">
                    <h4 class="font-medium mb-1">Samenvatting (uit Deel 1):</h4>
                    <p class="text-sm text-gray-600 dark:text-gray-300">{selectedDataFromPart1.summary}</p>
                </div>
            {/if}

            <div class="border border-gray-300 rounded-md p-3 bg-gray-50 dark:bg-gray-700">
                 <h4 class="font-medium mb-1">Criteria (uit Deel 1):</h4>
                 {#if selectedDataFromPart1.criteria.length > 0}
                    <ul class="list-disc list-inside space-y-1 text-sm text-gray-600 dark:text-gray-300">
                        {#each selectedDataFromPart1.criteria as criterion (criterion.id)}
                            <li>{criterion.text}</li>
                        {/each}
                    </ul>
                 {:else}
                    <p class="text-sm text-gray-500 dark:text-gray-400">Geen criteria gevonden in deel 1.</p>
                 {/if}
            </div>

            <!-- Voeg hier de logica en UI voor Deel 2 toe, gebruikmakend van selectedDataFromPart1 -->
            <p class="mt-4 text-gray-700 dark:text-gray-300">
                Hier komt de verdere verwerking of analyse van de geselecteerde subsidie criteria...
            </p>

        </div>
    {:else}
        <div class="text-center text-gray-500 dark:text-gray-400 py-10">
            <p>Selecteer alstublieft eerst een opgeslagen resultaat in Deel 1.</p>
            <!-- Optioneel: Link terug naar deel 1 -->
            <a href="/app-launcher/subsidies" class="text-blue-600 hover:underline mt-2 inline-block">Ga naar Deel 1</a>
        </div>
    {/if}
</div>

<style>
    /* Add any specific styles for subsidies2 here */
</style>