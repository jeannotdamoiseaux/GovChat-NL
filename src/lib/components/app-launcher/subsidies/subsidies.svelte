<script lang="ts">
    import { WEBUI_BASE_URL } from '$lib/constants';
    import { models, settings, user } from '$lib/stores';
    import { toast } from 'svelte-sonner';
    import { fade } from 'svelte/transition';
    import { onMount } from 'svelte';
    import { subsidyStore, fetchSavedOutputs, initializeStore, setSelectedOutput, addSavedOutput, clearSavedOutputs, saveSelection, loadLastSelection, setGlobalSelection, loadGlobalSelection } from '$lib/stores/subsidyStore';
    import type { SubsidyResponse } from '$lib/stores/subsidyStore';

    let userInput: string = '';
    let responseData: SubsidyResponse | null = null;
    let isLoading: boolean = false;
    let error: string | null = null;

    let fileInput: HTMLInputElement;
    let isProcessingFile = false;
    let isFlashing = false;
    let fileProcessingProgress = 0;
    let fileProcessingInterval: ReturnType<typeof setInterval> | null = null;

    onMount(async () => {
        // Initialiseer expliciet bij het laden
        initializeStore();
        
        try {
            // Haal eerst alle opgeslagen criteria op
            await fetchSavedOutputs();
            
            // Probeer eerst de globale selectie te laden
            const globalSelection = await loadGlobalSelection();
            
            if (globalSelection) {
                console.log("Globale standaard selectie geladen:", globalSelection.name);
                toast.success(`Globale standaard selectie "${globalSelection.name}" geladen`);
                return; // Stop hier als er een globale selectie is
            }
            
            // Als er geen globale selectie is, probeer dan de persoonlijke selectie
            const lastSelection = await loadLastSelection();
            if (lastSelection) {
                console.log("Persoonlijke selectie geladen:", lastSelection.name);
                toast.success(`Selectie "${lastSelection.name}" geladen`);
            }
        } catch (error) {
            console.error("Fout bij laden van selecties:", error);
            toast.error("Kon selecties niet laden");
        }
    });

    async function handleSubmit() {
        if (!userInput.trim()) {
            error = 'Voer alstublieft de regeling in.';
            toast.error(error);
            return;
        }
        const currentModelId = $settings?.models?.[0];
        if (!currentModelId) {
            error = 'Selecteer alstublieft een model in de navigatiebalk.';
            toast.error(error);
            return;
        }
        isLoading = true;
        error = null;
        responseData = null;
        setSelectedOutput(null);
        try {
            const backendUrl = WEBUI_BASE_URL || 'http://localhost:8080';
            const res = await fetch(`${backendUrl}/api/subsidies/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    user_input: userInput,
                    model: currentModelId
                })
            });
            if (!res.ok) {
                const errorData = await res.json().catch(() => ({ detail: 'Onbekende fout' }));
                throw new Error(errorData.detail || `HTTP error! status: ${res.status}`);
            }
            responseData = await res.json();
        } catch (e: any) {
            console.error('Fout bij ophalen subsidie-Criteria:', e);
            error = `Er is een fout opgetreden: ${e.message || 'Kon de server niet bereiken.'}`;
            toast.error(error);
        } finally {
            isLoading = false;
        }
    }

    async function handleFileUpload(event: Event | DragEvent) {
        let file: File | null = null;

        if (event instanceof DragEvent && event.dataTransfer?.files) {
            file = event.dataTransfer.files[0];
        } else if (event.target instanceof HTMLInputElement && event.target.files) {
            file = event.target.files[0];
        }

        if (!file) return;

        if (!file.name.match(/\.(doc|docx|pdf|txt|rtf)$/i)) {
            toast.error('Alleen Word, PDF, TXT of RTF bestanden zijn toegestaan');
            return;
        }

        isProcessingFile = true;
        isFlashing = true;
        fileProcessingProgress = 0;
        if (fileProcessingInterval) clearInterval(fileProcessingInterval);

        fileProcessingInterval = setInterval(() => {
            if (fileProcessingProgress < 99) {
                fileProcessingProgress += 1;
            } else {
                if (fileProcessingInterval) clearInterval(fileProcessingInterval);
                fileProcessingInterval = null;
            }
        }, 30);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const uploadResponse = await fetch(`${WEBUI_BASE_URL}/api/v1/files`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: formData
            });

            if (!uploadResponse.ok) {
                const errorData = await uploadResponse.json().catch(() => ({ detail: 'Fout bij uploaden bestand' }));
                throw new Error(errorData.detail || 'Fout bij uploaden bestand');
            }

            const uploadData = await uploadResponse.json();

            if (uploadData.content) {
                userInput = uploadData.content;
            } else if (uploadData.id) {
                const contentResponse = await fetch(`${WEBUI_BASE_URL}/api/v1/files/${uploadData.id}/data/content`, {
                    method: 'GET',
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
                });
                if (!contentResponse.ok) {
                    throw new Error('Fout bij ophalen bestandsinhoud na upload');
                }
                const textData = await contentResponse.json();
                userInput = textData.content;
            } else {
                throw new Error('Onbekend antwoordformaat van upload endpoint');
            }

            toast.success('Bestand succesvol geüpload en inhoud ingevoegd.');

        } catch (err: any) {
            console.error('Error processing file:', err);
            toast.error(`Fout bij verwerken bestand: ${err.message}`);
            userInput = '';
        } finally {
            if (fileProcessingInterval) clearInterval(fileProcessingInterval);
            fileProcessingInterval = null;
            fileProcessingProgress = 100;
            isProcessingFile = false;

            if (fileInput) fileInput.value = '';

            setTimeout(() => {
                isFlashing = false;
            }, 1000);
        }
    }

    function saveCurrentOutput() {
        if (responseData) {
            const name = prompt("Geef een naam op voor deze opgeslagen versie:", `Resultaat ${new Date().toLocaleTimeString()}`);
            if (name === null) {
                toast.info("Opslaan geannuleerd.");
                return;
            }
            if (!name.trim()) {
                toast.error("Naam mag niet leeg zijn.");
                return;
            }

            addSavedOutput({
                ...responseData,
                name: name.trim()
            });
            toast.success(`Resultaat "${name.trim()}" opgeslagen (Totaal: ${$subsidyStore.savedOutputs.length})`);
            console.log("Opgeslagen outputs (Store):", $subsidyStore.savedOutputs);
        } else {
            toast.info('Er is geen resultaat om op te slaan.');
        }
    }

    function selectOutput(output: SubsidyResponse) {
        setSelectedOutput(output);
        toast.success(`"${output.name}" geselecteerd.`);
        console.log("Geselecteerde output (Store):", $subsidyStore.selectedOutput);
    }

    function handleClearOutputs() {
        clearSavedOutputs();
        toast.info('Opgeslagen resultaten gewist.');
    }

    async function handleSaveSelection() {
        if ($subsidyStore.selectedOutput) {
            try {
                // Controleer eerst of deze selectie al is opgeslagen
                const existingItem = $subsidyStore.savedOutputs.find(item => 
                    item.savedId === $subsidyStore.selectedOutput?.savedId);
                
                if (existingItem) {
                    toast.info("Deze selectie is al opgeslagen");
                    return;
                }
                
                const name = prompt("Geef een naam voor deze selectie:", 
                    $subsidyStore.selectedOutput.name || `Selectie ${new Date().toLocaleTimeString()}`);
                
                if (name === null) {
                    toast.info("Opslaan van selectie geannuleerd");
                    return;
                }
                
                const savedSelection = await saveSelection({
                    ...$subsidyStore.selectedOutput,
                    name: name.trim() || $subsidyStore.selectedOutput.name
                });
                
                toast.success(`Selectie "${name || 'Naamloos'}" opgeslagen in backend`);
                console.log("Opgeslagen selectie:", savedSelection);
            } catch (error) {
                console.error("Fout bij opslaan selectie:", error);
                toast.error(`Kon selectie niet opslaan: ${error.message}`);
            }
        } else {
            toast.error("Er is geen selectie om op te slaan");
        }
    }

    async function setAsGlobalStandard() {
        if (!$subsidyStore.selectedOutput) {
            toast.error("Selecteer eerst criteria om als standaard in te stellen");
            return;
        }

        try {
            const isAdmin = $user?.role === 'admin';
            if (!isAdmin) {
                toast.error("Alleen beheerders kunnen de standaard criteria instellen");
                return;
            }

            const success = await setGlobalSelection($subsidyStore.selectedOutput);
            
            if (success) {
                toast.success(`"${$subsidyStore.selectedOutput.name}" is nu de standaard selectie voor alle gebruikers`);
            } else {
                toast.error("Kon de selectie niet als standaard instellen");
            }
        } catch (error) {
            console.error("Fout bij instellen globale standaard:", error);
            toast.error(`Kon de standaard selectie niet instellen: ${error.message}`);
        }
    }
</script>

<div class="max-w-7xl mx-auto mt-6 space-y-6 px-4">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
            <h2 class="text-2xl font-bold text-gray-800 dark:text-white text-center mb-6">
                Admin Panel Subsidie Criteria
            </h2>

            <form on:submit|preventDefault={handleSubmit} class="space-y-4">
                <div>
                    <label for="subsidy-input" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Uw Regeling (of upload een bestand)
                    </label>
                    <div class="relative">
                        {#if isProcessingFile}
                            <div class="progress-line absolute inset-x-0 top-0 h-1 pointer-events-none overflow-hidden z-10">
                                <div class="line"></div>
                            </div>
                        {/if}
                        <textarea
                            id="subsidy-input"
                            bind:value={userInput}
                            placeholder="Voer hier uw gehele subsidieregeling in..."
                            rows="5"
                            disabled={isLoading || isProcessingFile}
                            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 disabled:opacity-50 font-[system-ui] {isFlashing ? 'flash-animation' : ''}"
                            on:dragover|preventDefault
                            on:drop|preventDefault={handleFileUpload}
                        />
                        <div class="mt-2">
                            {#if isProcessingFile || fileProcessingProgress === 100}
                                <div class="flex items-center gap-2" transition:fade={{ duration: 150 }}>
                                    <div class="flex-grow bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                        <div
                                            class="bg-blue-600 h-2 rounded-full transition-all duration-150 ease-linear"
                                            style="width: {fileProcessingProgress}%"
                                        ></div>
                                    </div>
                                    <span class="text-sm text-gray-600 dark:text-gray-400 min-w-[3rem] text-right">{fileProcessingProgress}%</span>
                                </div>
                            {/if}
                            <div class="mt-2 flex items-center justify-between gap-2">
                                <div class="flex items-center gap-2">
                                    <input
                                        type="file"
                                        accept=".doc,.docx,.pdf,.txt,.rtf"
                                        class="hidden"
                                        bind:this={fileInput}
                                        on:change={handleFileUpload}
                                    />
                                    <button
                                        type="button"
                                        on:click={() => fileInput.click()}
                                        disabled={isProcessingFile || isLoading}
                                        class="bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-white font-medium py-1 px-3 rounded focus:outline-none focus:shadow-outline flex items-center gap-2 disabled:opacity-50"
                                    >
                                        {#if isProcessingFile}
                                            <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                            <span>Uploaden...</span>
                                        {:else if !isProcessingFile && fileProcessingProgress === 100}
                                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                                            <span>Bestand geüpload</span>
                                        {:else}
                                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3 3m0 0l-3-3m3 3V8" /></svg>
                                            <span>Upload bestand</span>
                                        {/if}
                                    </button>
                                </div>
                                <span class="text-sm text-gray-500 dark:text-gray-400 text-right">
                                    of sleep bestand hierheen<br>(Word, PDF, TXT, RTF)
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={isLoading || isProcessingFile || !$settings?.models?.[0]}
                    class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                    {#if isLoading}
                        <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                        Verwerken...
                    {:else if isProcessingFile}
                        Bestand verwerken...
                    {:else if !$settings?.models?.[0]}
                        Selecteer een model in de navigatiebalk
                    {:else}
                        Haal relevante Criteria uit subsidieregelingen
                    {/if}
                </button>
            </form>
        </div>

        {#if $subsidyStore.savedOutputs.length > 0}
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
                <h3 class="text-xl font-bold text-gray-800 dark:text-white mb-4">Opgeslagen Resultaten ({$subsidyStore.savedOutputs.length})</h3>
                <ul class="space-y-3 max-h-[calc(100vh-20rem)] overflow-y-auto pr-2">
                    {#each $subsidyStore.savedOutputs.filter(output => 
                        output.criteria && 
                        output.criteria.length > 0 && 
                        (!output.name.includes("Naamloos") || output.criteria.length > 0)
                    ) as savedOutput (savedOutput.savedId)}
                        <li class="border border-gray-200 dark:border-gray-700 rounded p-3 flex justify-between items-center {$subsidyStore.selectedOutput?.savedId === savedOutput.savedId ? 'bg-blue-100 dark:bg-blue-900/50 ring-2 ring-blue-500' : 'bg-gray-50 dark:bg-gray-700/50'}">
                            <div>
                                <p class="font-semibold text-gray-800 dark:text-gray-200">
                                    {savedOutput.name || 'Resultaat'}
                                </p>
                                <p class="text-sm text-gray-500 dark:text-gray-400">
                                    Opgeslagen: {savedOutput.timestamp?.toLocaleString() ?? 'Onbekend'}
                                    ({savedOutput.criteria.length} criteria)
                                </p>
                            </div>
                            <button
                                type="button"
                                on:click={() => selectOutput(savedOutput)}
                                class="ml-4 px-3 py-1 text-sm rounded focus:outline-none focus:ring-2 focus:ring-offset-1 {$subsidyStore.selectedOutput?.savedId === savedOutput.savedId ? 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500' : 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-500 focus:ring-gray-400'}"
                                title="Selecteer dit resultaat om te gebruiken"
                            >
                                {$subsidyStore.selectedOutput?.savedId === savedOutput.savedId ? 'Geselecteerd' : 'Selecteer'}
                            </button>
                        </li>
                    {/each}
                </ul>
                <div class="mt-4 flex justify-end">
                    <button
                        type="button"
                        on:click={handleClearOutputs}
                        class="text-sm text-red-600 hover:text-red-800 dark:text-red-500 dark:hover:text-red-400"
                    >
                        Wis Alle Opgeslagen Resultaten
                    </button>
                </div>
            </div>
        {:else}
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-5 flex items-center justify-center text-gray-500 dark:text-gray-400 min-h-[10rem]">
                <span>Nog geen resultaten opgeslagen.</span>
            </div>
        {/if}
    </div>

    {#if responseData || isLoading}
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
            {#if isLoading}
                <div class="flex justify-center items-center h-40">
                     <svg class="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                </div>
            {:else if responseData}
                <div class="space-y-4">
                    {#if responseData.summary}
                        <div class="border border-gray-300 rounded-md p-4 bg-gray-50 dark:bg-gray-700 dark:border-gray-600">
                            <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-2">Samenvatting:</h3>
                            <p class="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{responseData.summary}</p>
                        </div>
                    {/if}
                    <div class="border border-gray-300 rounded-md p-4 bg-gray-50 dark:bg-gray-700 dark:border-gray-600">
                        <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-2">Geëxtraheerde Criteria:</h3>
                        {#if responseData.criteria && responseData.criteria.length > 0}
                            <ul class="list-disc list-inside space-y-2">
                                {#each responseData.criteria as criterion (criterion.id)}
                                    <li class="text-gray-700 dark:text-gray-300">{criterion.text}</li>
                                {/each}
                            </ul>
                        {:else}
                            <p class="text-gray-500 dark:text-gray-400">Geen criteria gevonden.</p>
                        {/if}
                    </div>
                    <div class="flex justify-end">
                        <button
                            type="button"
                            on:click={saveCurrentOutput}
                            class="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline flex items-center gap-2"
                            title="Voeg dit resultaat toe aan de lijst en geef een naam op"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" /></svg>
                            Sla Resultaat Op Met Naam...
                        </button>
                    </div>
                </div>
            {/if}
        </div>
    {/if}

    {#if $subsidyStore.selectedOutput}
        <div class="bg-blue-50 dark:bg-blue-900/30 border border-blue-300 dark:border-blue-700 rounded-lg shadow p-5">
            <h3 class="text-lg font-semibold text-blue-800 dark:text-blue-200 mb-2">Geselecteerd Resultaat: "{$subsidyStore.selectedOutput.name}"</h3>
            {#if $subsidyStore.selectedOutput.summary}
                <p class="text-sm text-blue-700 dark:text-blue-300 mb-2"><strong>Samenvatting:</strong> {$subsidyStore.selectedOutput.summary}</p>
            {/if}
            <p class="text-sm text-blue-700 dark:text-blue-300"><strong>Aantal criteria:</strong> {$subsidyStore.selectedOutput.criteria.length}</p>
        
            <!-- Nieuwe knop om selectie op te slaan naar backend -->
            <div class="mt-4 flex justify-end">
                <button
                    type="button"
                    on:click={() => {
                        // Ga direct naar deel 2
                        window.location.href = '/app-launcher/subsidies2';
                    }}
                    class="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline flex items-center gap-2 mr-2"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                    </svg>
                    Ga naar beoordelingstool
                </button>
                
                <button
                    type="button"
                    on:click={handleSaveSelection}
                    class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline flex items-center gap-2"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                    </svg>
                    Maak kopie van selectie
                </button>
            </div>
        </div>
    {/if}

    {#if $subsidyStore.selectedOutput && $user?.role === 'admin'}
        <button
            type="button"
            on:click={setAsGlobalStandard}
            class="mt-2 bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline flex items-center gap-2 w-full"
        >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            Maak dit de standaardcriteria voor alle gebruikers
        </button>
    {/if}
</div>

<style>
  .progress-line {
    background-color: rgba(59, 130, 246, 0.1);
  }
  .progress-line .line {
    height: 100%;
    background-color: #3b82f6;
    animation: progress 2s infinite;
    width: 100%;
    transform-origin: left;
  }
  @keyframes progress {
    0% { transform: translateX(-100%); }
    50% { transform: translateX(0); }
    100% { transform: translateX(100%); }
  }

  @keyframes flash {
    0% { background-color: rgba(59, 130, 246, 0); box-shadow: 0 0 0 0 rgba(96, 165, 250, 0); }
    15% { background-color: rgba(59, 130, 246, 0.2); box-shadow: 0 0 30px 15px rgba(96, 165, 250, 0.3), 0 0 0 30px rgba(96, 165, 250, 0.1), inset 0 0 15px rgba(255, 255, 255, 0.4); }
    30% { background-color: rgba(59, 130, 246, 0.1); box-shadow: 0 0 50px 20px rgba(96, 165, 250, 0.1), 0 0 0 40px rgba(96, 165, 250, 0), inset 0 0 20px rgba(255, 255, 255, 0.2); }
    100% { background-color: rgba(59, 130, 246, 0); box-shadow: 0 0 0 0 rgba(96, 165, 250, 0); }
  }
  :global(.flash-animation) {
    animation: flash 1.0s cubic-bezier(0.4, 0, 0.2, 1);
    border-color: rgba(96, 165, 250, 0.8);
    position: relative;
  }
</style>