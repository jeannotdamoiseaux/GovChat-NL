<script>
    import { onMount, getContext } from 'svelte';
    import { models as modelsStore } from '$lib/stores';
    import { WEBUI_BASE_URL } from '$lib/constants';
    import { fade } from 'svelte/transition';
    import { toast } from 'svelte-sonner';
  
    const i18n = getContext('i18n');
  
    // Props - ontvang selectedModels van de parent component
    export let selectedModels = [''];
  
    let inputText = '';
    let outputText = '';
    let isLoading = false;
    let error = null;
    let preservedWords = []; // Door gebruiker toegevoegde woorden
    let newPreservedWord = '';
    let models = [];
    let showOutput = false;
    let languageLevel = 'B1';
    let textFragments = new Map();
    let partialFragments = new Map();
  
    // Gebruik de modelsStore om modellen op te halen
    const unsubscribe = modelsStore.subscribe(value => {
      models = value;
    });
  
    // Functie om geselecteerde modellen te laden uit localStorage
    function loadSelectedModels() {
      try {
        const savedModels = localStorage.getItem('b1_taalniveau_selected_models');
        if (savedModels) {
          const parsedModels = JSON.parse(savedModels);
          if (Array.isArray(parsedModels) && parsedModels.length > 0) {
            selectedModels = parsedModels;
          }
        }
      } catch (error) {
        console.error("Error loading saved models:", error);
      }
    }
  
    onMount(() => {
      // Laad opgeslagen modellen
      loadSelectedModels();
      
      // Cleanup subscription when component is destroyed
      return () => {
        unsubscribe();
      };
    });
  
    // Functie om een woord toe te voegen aan de lijst van te behouden woorden
    function addPreservedWord() {
      if (newPreservedWord.trim()) {
        preservedWords = [...preservedWords, newPreservedWord.trim()];
        newPreservedWord = '';
      }
    }
  
    // Functie om een woord te verwijderen uit de lijst van door gebruiker toegevoegde woorden
    function removePreservedWord(word) {
      preservedWords = preservedWords.filter(w => w !== word);
    }
  
    // Functie om te schakelen tussen B1 en B2 taalniveau
    function toggleLanguageLevel() {
      languageLevel = languageLevel === 'B1' ? 'B2' : 'B1';
    }
  
    async function simplifyText() {
      if (!inputText.trim()) {
        error = "Voer tekst in om te vereenvoudigen";
        return;
      }
  
      if (!selectedModels[0]) {
        error = "Selecteer eerst een model in de navigatiebalk linksboven";
        return;
      }
  
      error = null;
      isLoading = true;
      showOutput = true; // Show output container immediately
      outputText = ''; // Clear previous output
  
      try {
        const token = localStorage.getItem('token');
        const payload = {
          model: selectedModels[0],
          text: inputText,
          preserved_words: preservedWords,
          language_level: languageLevel
        };
  
        // Use fetch with streaming response handling
        const response = await fetch(`${WEBUI_BASE_URL}/api/b1/translate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(payload)
        });
  
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
  
        // Handle streaming response
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          // Decode the chunk and process it
          const chunk = decoder.decode(value, { stream: true });
          
          // Process SSE format (data: {...}\n\n)
          const lines = chunk.split('\n');
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const jsonStr = line.substring(6).trim(); // Remove 'data: ' prefix and trim whitespace
                if (jsonStr === '[DONE]') continue;
                
                const jsonData = JSON.parse(jsonStr);
                // Handle positioned text updates
                if (jsonData.text && typeof jsonData.position === 'number') {
                  if (jsonData.isPartial) {
                    // Voeg woord toe aan partial fragment
                    const currentPartial = partialFragments.get(jsonData.position) || '';
                    partialFragments.set(jsonData.position, currentPartial + jsonData.text);
                  } else {
                    // Paragraaf is compleet
                    textFragments.set(jsonData.position, partialFragments.get(jsonData.position) || '');
                    partialFragments.delete(jsonData.position);
                  }

                  // Reconstrueer volledige tekst
                  let orderedText = '';
                  const sortedPositions = Array.from(textFragments.keys()).sort((a, b) => a - b);
                  
                  for (const pos of sortedPositions) {
                    orderedText += textFragments.get(pos);
                    // Voeg partial fragment toe als het bestaat
                    if (partialFragments.has(pos)) {
                      orderedText += partialFragments.get(pos);
                    }
                  }
                  
                  // Update output
                  outputText = orderedText.trim();
                }
              } catch (e) {
                console.warn('Error parsing SSE data:', e);
              }
            }
          }
        }
        
        // Sla de geselecteerde modellen op voor later gebruik
        localStorage.setItem('b1_taalniveau_selected_models', JSON.stringify(selectedModels));
      } catch (err) {
        console.error("Error simplifying text:", err);
        error = "Fout bij vereenvoudigen: " + (err.message || "Onbekende fout");
        showOutput = false;
      } finally {
        isLoading = false;
      }
    }
  </script>
  
  <div class="max-w-7xl mx-auto mt-10">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold text-gray-800 dark:text-white">
          {languageLevel}-Taalniveau Vereenvoudiger
        </h1>
        
        <!-- Taalniveau schakelaar -->
        <div class="flex items-center">
          <span class="mr-2 text-sm text-gray-600 dark:text-gray-400">Taalniveau:</span>
          <button 
            on:click={toggleLanguageLevel}
            class="relative inline-flex items-center h-6 rounded-full w-11 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 {languageLevel === 'B2' ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'}"
          >
            <span class="sr-only">Schakel taalniveau</span>
            <span 
              class="inline-block w-4 h-4 transform bg-white rounded-full transition-transform {languageLevel === 'B2' ? 'translate-x-6' : 'translate-x-1'}"
            ></span>
          </button>
          <span class="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300">{languageLevel}</span>
        </div>
      </div>
      
      {#if error}
        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      {/if}
      
      <!-- Sectie voor woorden die behouden moeten blijven -->
      <div class="mb-4">
        <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Woorden die niet vereenvoudigd mogen worden:
        </h3>
        
        <div class="flex mb-2">
          <input
            type="text"
            bind:value={newPreservedWord}
            placeholder="Voer een woord of term in"
            class="flex-grow px-3 py-2 border border-gray-300 rounded-l-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            on:keydown={(e) => e.key === 'Enter' && addPreservedWord()}
          />
          <button
            on:click={addPreservedWord}
            class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-r-md focus:outline-none focus:shadow-outline"
          >
            Toevoegen
          </button>
        </div>
        
        <!-- Door gebruiker toegevoegde woorden -->
        {#if preservedWords.length > 0}
          <div class="mt-2">
            <div class="flex flex-wrap gap-2 mt-2">
              {#each preservedWords as word}
                <div class="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 px-2 py-1 rounded-md flex items-center">
                  <span>{word}</span>
                  <button 
                    on:click={() => removePreservedWord(word)}
                    class="ml-2 text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200 focus:outline-none"
                  >
                    ×
                  </button>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>
      
      <!-- Flex container voor input en output naast elkaar -->
      <div class="flex flex-col md:flex-row gap-6">
        <!-- Linker kolom: Input -->
        <div class="flex-1">
          <label for="input" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Originele tekst
          </label>
          <div class="relative">
            <textarea
              id="input"
              bind:value={inputText}
              rows="12"
              draggable="false"
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white min-h-[288px] max-h-[288px] overflow-y-auto"
              placeholder="Voer hier de tekst in die je wilt vereenvoudigen naar {languageLevel}-taalniveau..."
              disabled={isLoading}
            ></textarea>
          </div>
        </div>
        
        <!-- Midden: Vertaalknop voor kleine schermen -->
        <div class="md:hidden w-full">
          <button 
            on:click={simplifyText}
            disabled={isLoading || !selectedModels[0]}
            class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50"
          >
            {#if !selectedModels[0]}
              Selecteer eerst een model in de navigatiebalk linksboven
            {:else if isLoading}
              <div class="flex items-center justify-center">
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Bezig met vereenvoudigen...
              </div>
            {:else}
              Vereenvoudig naar {languageLevel}-taalniveau
            {/if}
          </button>
        </div>
        
        <!-- Midden: Vertaalpijl voor grotere schermen -->
        <div class="hidden md:flex flex-col items-center justify-center">
          <button 
            on:click={simplifyText}
            disabled={isLoading || !selectedModels[0]}
            class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-full focus:outline-none focus:shadow-outline disabled:opacity-50 h-12 w-12 flex items-center justify-center"
            title="Vereenvoudig naar {languageLevel}-taalniveau"
          >
            {#if isLoading}
              <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            {:else}
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            {/if}
          </button>
        </div>
        
        <!-- Rechter kolom: Output -->
        <div class="flex-1">
          <label for="output" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {languageLevel}-taalniveau tekst
          </label>
          
          <div class="relative">
            {#if isLoading}
              <!-- Show loading indicators while still displaying partial results -->
              <div class="progress-line absolute inset-x-0 top-0 h-1 pointer-events-none overflow-hidden">
                <div class="line"></div>
              </div>
            {/if}
            
            {#if showOutput}
              <div 
                id="output"
                class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white min-h-[288px] max-h-[288px] overflow-y-auto"
                transition:fade={{ duration: 200 }}
              >
                {outputText}
              </div>
              
              <div class="mt-4 flex justify-end">
                <button
                on:click={() => {
                    navigator.clipboard.writeText(outputText)
                      .then(() => {
                        toast.success('Tekst gekopieerd naar klembord!');
                      })
                      .catch(err => {
                        console.error('Kon niet kopiëren:', err);
                        toast.error('Kon niet kopiëren: ' + err);
                      });
                  }}
                  class="bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-white font-medium py-1 px-3 rounded focus:outline-none focus:shadow-outline"
                >
                  Kopieer naar klembord
                </button>
              </div>
            {:else if !isLoading}
              <div class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-400 min-h-[288px] flex items-center justify-center">
                <p>Hier verschijnt de vereenvoudigde tekst na verwerking</p>
              </div>
            {/if}
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <style>
    /* Loading spinner */
    .loading-spinner {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      border: 3px solid rgba(59, 130, 246, 0.1);
      border-top-color: #3b82f6;
      animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    
    /* Progress line animation */
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
  </style>
