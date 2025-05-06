<script lang="ts">
    import { WEBUI_BASE_URL } from '$lib/constants';
    import { models, settings } from '$lib/stores';
    import { subsidyStore } from '$lib/stores/subsidyStore';
    import type { SubsidyResponse } from '$lib/stores/subsidyStore';
    import { onMount } from 'svelte';
    import { toast } from 'svelte-sonner';
    import { fade } from 'svelte/transition';

    // Subscribe aan de geselecteerde output uit de store
    let selectedDataFromPart1: SubsidyResponse | null = null;
    
    // Aanvraag tekst input
    let applicationText: string = '';
    
    // Beoordeling resultaten
    let assessmentResults: Record<string, {Criterium: string, Score: string, Toelichting: string}> | null = null;
    
    // Samenvatting resultaat
    let summaryResult: {
        Aanvrager: string,
        Datum_aanvraag: string,
        Datum_evenement: string,
        Bedrag: string,
        Samenvatting: string
    } | null = null;
    
    // Status tracking
    let isLoading: boolean = false;
    let error: string | null = null;
    
    // Status voor samenvatting
    let isLoadingSummary: boolean = false;
    let summaryError: string | null = null;

    const unsubscribe = subsidyStore.subscribe(store => {
        selectedDataFromPart1 = store.selectedOutput;
    });

    onMount(() => {
        // Optioneel: Log de data wanneer het component mount
        console.log("Data ontvangen van Deel 1:", selectedDataFromPart1);

        // Cleanup de subscription wanneer het component unmount
        return () => unsubscribe();
    });

    async function handleAssessmentSubmit() {
        if (!selectedDataFromPart1?.criteria || selectedDataFromPart1.criteria.length === 0) {
            toast.error("Er zijn geen criteria geselecteerd om te beoordelen");
            return;
        }
        
        if (!applicationText.trim()) {
            toast.error("Voer alstublieft een subsidieaanvraag in om te beoordelen");
            return;
        }
        
        // Zorg voor een geldig model
        // Probeer eerst de modelnaam uit de store te halen
        let currentModelId = $settings?.models?.[0];
        
        // Als fallback, gebruik een hardgecodeerd model dat zeker beschikbaar is
        if (!currentModelId) {
            toast.warn("Geen model geselecteerd, gebruiken standaard model");
            currentModelId = "openai/gpt-4o"; // Standaard model dat waarschijnlijk beschikbaar is
        }
        
        isLoading = true;
        error = null;
        assessmentResults = null;
        
        console.log("Model dat gebruikt wordt:", currentModelId);
        
        try {
            const backendUrl = WEBUI_BASE_URL || 'http://localhost:8080';
            const res = await fetch(`${backendUrl}/api/subsidies/assess`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    application_text: applicationText,
                    criteria: selectedDataFromPart1.criteria,
                    model: currentModelId
                })
            });
            
            if (!res.ok) {
                const errorData = await res.json().catch(() => ({ detail: 'Onbekende fout' }));
                throw new Error(errorData.detail || `HTTP error! status: ${res.status}`);
            }
            
            const responseData = await res.json();
            assessmentResults = responseData.assessment;
            toast.success("Beoordeling succesvol afgerond!");
            
        } catch (e: any) {
            console.error('Fout bij beoordelen subsidieaanvraag:', e);
            error = `Er is een fout opgetreden: ${e.message || 'Kon de server niet bereiken.'}`;
            toast.error(error);
        } finally {
            isLoading = false;
        }
    }

    async function handleSummaryRequest() {
        if (!applicationText.trim()) {
            toast.error("Voer alstublieft een subsidieaanvraag in om samen te vatten");
            return;
        }
        
        const currentModelId = $settings?.models?.[0];
        if (!currentModelId) {
            toast.warn("Geen model geselecteerd, standaard model wordt gebruikt");
        }
        
        isLoadingSummary = true;
        summaryError = null;
        summaryResult = null;
        
        try {
            const backendUrl = WEBUI_BASE_URL || 'http://localhost:8080';
            const res = await fetch(`${backendUrl}/api/subsidies/summarize`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    application_text: applicationText,
                    criteria: selectedDataFromPart1?.criteria || [],
                    model: currentModelId
                })
            });
            
            if (!res.ok) {
                const errorData = await res.json().catch(() => ({ detail: 'Onbekende fout' }));
                throw new Error(errorData.detail || `HTTP error! status: ${res.status}`);
            }
            
            summaryResult = await res.json();
            toast.success("Samenvatting succesvol gegenereerd!");
            
        } catch (e: any) {
            console.error('Fout bij genereren samenvatting:', e);
            summaryError = `Er is een fout opgetreden: ${e.message || 'Kon de server niet bereiken.'}`;
            toast.error(summaryError);
        } finally {
            isLoadingSummary = false;
        }
    }

    function getScoreColorClass(score: string): string {
        if (score === 'Onzeker') return 'text-yellow-600 dark:text-yellow-400';
        const numScore = parseInt(score);
        if (isNaN(numScore)) return '';
        
        if (numScore >= 8) return 'text-green-600 dark:text-green-400';
        if (numScore >= 5) return 'text-blue-600 dark:text-blue-400';
        if (numScore >= 3) return 'text-yellow-600 dark:text-yellow-400';
        return 'text-red-600 dark:text-red-400';
    }
</script>

<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
    <h2 class="text-2xl font-bold text-gray-800 dark:text-white text-center mb-6">
        Subsidie Beoordeling
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
                    <div class="max-h-40 overflow-y-auto">
                        <ul class="list-disc list-inside space-y-1 text-sm text-gray-600 dark:text-gray-300">
                            {#each selectedDataFromPart1.criteria as criterion (criterion.id)}
                                <li>{criterion.text}</li>
                            {/each}
                        </ul>
                    </div>
                 {:else}
                    <p class="text-sm text-gray-500 dark:text-gray-400">Geen criteria gevonden in deel 1.</p>
                 {/if}
            </div>

            <!-- Subsidieaanvraag invoer -->
            <div class="mt-6 bg-gray-50 dark:bg-gray-700 rounded-lg p-4 border border-gray-300 dark:border-gray-600">
                <h4 class="text-lg font-semibold text-gray-800 dark:text-white mb-3">
                    Beoordeel uw subsidieaanvraag
                </h4>
                
                <div class="space-y-4">
                    <div>
                        <label for="application-text" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Uw subsidieaanvraag tekst
                        </label>
                        <textarea
                            id="application-text"
                            bind:value={applicationText}
                            placeholder="Voer hier uw subsidieaanvraag in om te beoordelen tegen de geselecteerde criteria..."
                            rows="8"
                            disabled={isLoading}
                            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-white dark:bg-gray-800 dark:border-gray-600 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
                        ></textarea>
                    </div>

                    <div class="flex space-x-2 mt-3">
                        <button
                            type="button"
                            on:click={handleAssessmentSubmit}
                            disabled={isLoading || !applicationText.trim() || !$settings?.models?.[0]}
                            class="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                        >
                            {#if isLoading}
                                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Beoordeling Verwerken...
                            {:else}
                                Beoordeel Aanvraag
                            {/if}
                        </button>
                        
                        <button
                            type="button"
                            on:click={handleSummaryRequest}
                            disabled={isLoadingSummary || !applicationText.trim()}
                            class="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                        >
                            {#if isLoadingSummary}
                                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Genereren...
                            {:else}
                                Genereer Samenvatting
                            {/if}
                        </button>
                    </div>
                </div>
            </div>

            {#if error}
                <div class="bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-lg p-3 text-red-800 dark:text-red-300">
                    <p class="font-medium">Er is een fout opgetreden:</p>
                    <p>{error}</p>
                </div>
            {/if}

            <!-- Samenvatting -->
            {#if summaryResult}
                <div class="mt-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 shadow-sm" transition:fade={{ duration: 300 }}>
                    <h3 class="text-xl font-bold text-green-800 dark:text-green-400 mb-3">
                        Samenvatting Aanvraag
                    </h3>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="space-y-2">
                            <div>
                                <h4 class="font-semibold text-green-700 dark:text-green-300">Aanvrager</h4>
                                <p class="text-gray-800 dark:text-gray-200">{summaryResult.Aanvrager}</p>
                            </div>
                            
                            <div>
                                <h4 class="font-semibold text-green-700 dark:text-green-300">Datum aanvraag</h4>
                                <p class="text-gray-800 dark:text-gray-200">{summaryResult.Datum_aanvraag}</p>
                            </div>
                            
                            <div>
                                <h4 class="font-semibold text-green-700 dark:text-green-300">Datum evenement</h4>
                                <p class="text-gray-800 dark:text-gray-200">{summaryResult.Datum_evenement}</p>
                            </div>
                            
                            <div>
                                <h4 class="font-semibold text-green-700 dark:text-green-300">Bedrag</h4>
                                <p class="text-gray-800 dark:text-gray-200">{summaryResult.Bedrag}</p>
                            </div>
                        </div>
                        
                        <div>
                            <h4 class="font-semibold text-green-700 dark:text-green-300">Samenvatting</h4>
                            <p class="text-gray-800 dark:text-gray-200">{summaryResult.Samenvatting}</p>
                        </div>
                    </div>
                </div>
            {/if}

            {#if summaryError}
                <div class="mt-4 bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700 rounded-lg p-3 text-red-800 dark:text-red-300">
                    <p class="font-medium">Er is een fout opgetreden bij het genereren van de samenvatting:</p>
                    <p>{summaryError}</p>
                </div>
            {/if}

            <!-- Beoordelingsresultaten -->
            {#if assessmentResults}
                <div class="mt-8 space-y-4" transition:fade={{ duration: 300 }}>
                    <h3 class="text-xl font-bold text-gray-800 dark:text-white border-b pb-2">
                        Beoordelingsresultaten
                    </h3>
                    
                    <div class="border border-gray-300 dark:border-gray-600 rounded-md overflow-hidden">
                        <table class="min-w-full divide-y divide-gray-300 dark:divide-gray-700">
                            <thead class="bg-gray-50 dark:bg-gray-700">
                                <tr>
                                    <th scope="col" class="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                        #
                                    </th>
                                    <th scope="col" class="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                        Criterium
                                    </th>
                                    <th scope="col" class="px-3 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider w-20">
                                        Score
                                    </th>
                                    <th scope="col" class="px-3 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                        Toelichting
                                    </th>
                                </tr>
                            </thead>
                            <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                                {#each Object.entries(assessmentResults) as [key, assessment] (key)}
                                    <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                                        <td class="px-3 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white font-medium">
                                            {key}
                                        </td>
                                        <td class="px-3 py-4 text-sm text-gray-700 dark:text-gray-300">
                                            {assessment.Criterium}
                                        </td>
                                        <td class="px-3 py-4 whitespace-nowrap text-sm text-center font-bold {getScoreColorClass(assessment.Score)}">
                                            {assessment.Score}
                                        </td>
                                        <td class="px-3 py-4 text-sm text-gray-700 dark:text-gray-300">
                                            {assessment.Toelichting}
                                        </td>
                                    </tr>
                                {/each}
                            </tbody>
                        </table>
                    </div>
                </div>
            {/if}
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