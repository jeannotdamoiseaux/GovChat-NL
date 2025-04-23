<script lang="ts">
    import { WEBUI_BASE_URL } from '$lib/constants';
    import { models, settings } from '$lib/stores';
    import { toast } from 'svelte-sonner';
    import { fade } from 'svelte/transition'; // Import fade transition

    let userInput: string = '';
    let response: string | null = null;
    let isLoading: boolean = false; // Loading state for API call
    let error: string | null = null;

    // --- File Handling State ---
    let fileInput: HTMLInputElement; // Reference to the file input element
    let isProcessingFile = false; // Loading state for file processing
    let isFlashing = false; // For visual feedback on drop/upload
    let fileProcessingProgress = 0; // State for fake progress
    let fileProcessingInterval: ReturnType<typeof setInterval> | null = null; // Interval timer reference
    // --- End File Handling State ---

    async function handleSubmit() {
        if (!userInput.trim()) {
            error = 'Voer alstublieft een vraag in.';
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
        response = null;
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
            const data = await res.json();
            response = data.response;
        } catch (e: any) {
            console.error('Fout bij het ophalen van subsidie-informatie:', e);
            error = `Er is een fout opgetreden: ${e.message || 'Kon de server niet bereiken.'}`;
            toast.error(error);
        } finally {
            isLoading = false;
        }
    }

    // --- File Upload Function ---
    async function handleFileUpload(event: Event | DragEvent) {
        let file: File | null = null;

        if (event instanceof DragEvent && event.dataTransfer?.files) {
            file = event.dataTransfer.files[0];
        } else if (event.target instanceof HTMLInputElement && event.target.files) {
            file = event.target.files[0];
        }

        if (!file) return;

        // Validate file type
        if (!file.name.match(/\.(doc|docx|pdf|txt|rtf)$/i)) {
            toast.error('Alleen Word, PDF, TXT of RTF bestanden zijn toegestaan');
            return;
        }

        // --- Start Fake Progress ---
        isProcessingFile = true;
        isFlashing = true; // Start visual feedback
        fileProcessingProgress = 0; // Reset progress
        if (fileProcessingInterval) clearInterval(fileProcessingInterval);

        fileProcessingInterval = setInterval(() => {
            if (fileProcessingProgress < 99) {
                fileProcessingProgress += 1;
            } else {
                if (fileProcessingInterval) clearInterval(fileProcessingInterval);
                fileProcessingInterval = null;
            }
        }, 30); // Update interval
        // --- End Fake Progress Start ---

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
            userInput = ''; // Clear input on error
        } finally {
            if (fileProcessingInterval) clearInterval(fileProcessingInterval);
            fileProcessingInterval = null;
            fileProcessingProgress = 100; // Set to 100% on completion
            isProcessingFile = false; // Set processing to false *after* setting progress to 100

            if (fileInput) fileInput.value = ''; // Reset file input

            setTimeout(() => {
                isFlashing = false;
            }, 1000); // Duration of flash + delay
        }
    }
    // --- End File Upload Function ---

</script>

<div class="max-w-3xl mx-auto mt-6">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
        <h2 class="text-2xl font-bold text-gray-800 dark:text-white text-center mb-6">
            Admin Panel Subsidie Regeling
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
                        placeholder="Voer hier uw gehele subsidieregeling in, LAICA haalt de relevante informtie hier uit..."
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
                    Haal relevante informatie uit subsidieregelingen
                {/if}
            </button>
        </form>

        {#if response}
            <div class="mt-6 border border-gray-300 rounded-md p-4 bg-gray-50 dark:bg-gray-700 dark:border-gray-600">
                <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-2">Antwoord:</h3>
                <p class="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{response}</p>
            </div>
        {/if}
    </div>
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