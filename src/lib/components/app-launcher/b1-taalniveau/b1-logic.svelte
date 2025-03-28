<script>
  import { onMount } from 'svelte';
  import { user, models as modelsStore } from '$lib/stores';
  import { WEBUI_BASE_URL } from '$lib/constants';
  import { fade } from 'svelte/transition';
  
  // Props - ontvang selectedModels van de parent component
  export let selectedModels = [''];
  
  let inputText = '';
  let outputText = '';
  let isLoading = false;
  let error = null;
  let preservedWords = []; 
  let newPreservedWord = '';
  let models = [];
  let showOutput = false;
  // Nieuwe state variabele voor taalniveau
  let languageLevel = 'B1'; // Standaard op B1
  
  // Gebruik de modelsStore om modellen op te halen
  const unsubscribe = modelsStore.subscribe(value => {
    models = value;
  });

  onMount(() => {
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

  // Functie om een woord te verwijderen uit de lijst
  function removePreservedWord(index) {
    preservedWords = preservedWords.filter((_, i) => i !== index);
  }

  // Functie om te schakelen tussen B1 en B2 taalniveau
  function toggleLanguageLevel() {
    languageLevel = languageLevel === 'B1' ? 'B2' : 'B1';
  }

  async function translateToB1() {
    if (!inputText.trim()) {
      error = "Voer tekst in om te vertalen";
      return;
    }

    // Controleer of er een model is geselecteerd
    if (!selectedModels[0]) {
      error = "Selecteer eerst een model in de navigatiebalk linksboven";
      return;
    }

    error = null;
    isLoading = true;
    showOutput = false; // Hide output while loading
    outputText = ''; // Clear previous output while loading

    try {
      // Get the authentication token
      const token = localStorage.getItem('token');
      
      // Maak een payload voor de backend API
      const payload = {
        model: selectedModels[0],
        text: inputText,
        preserved_words: preservedWords,
        language_level: languageLevel // Voeg het geselecteerde taalniveau toe aan de payload
      };

      // Gebruik WEBUI_BASE_URL voor de API-aanroep
      const response = await fetch(`${WEBUI_BASE_URL}/api/b1/translate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (response.status === 403) {
        throw new Error("Je hebt geen toegang tot dit model. Probeer een ander model te selecteren.");
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      outputText = data.choices?.[0]?.message?.content || "Geen resultaat ontvangen";
      
      // Add a small delay before showing the output for a smoother transition
      setTimeout(() => {
        showOutput = true;
      }, 300);
      
    } catch (err) {
      console.error("Error translating:", err);
      error = "Fout bij vertalen: " + (err.message || "Onbekende fout");
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="max-w-7xl mx-auto">
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-800 dark:text-white">
        {languageLevel}-Taalniveau Vertaler
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
    
    <!-- Instructie voor model selectie -->
    <div class="mb-4 text-sm text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 p-3 rounded">
      {#if selectedModels[0]}
        <div class="font-medium">Geselecteerd model: <span class="text-blue-600 dark:text-blue-400">{models.find(m => m.id === selectedModels[0])?.name || selectedModels[0]}</span></div>
      {:else}
        <div class="font-medium text-yellow-600">Geen model geselecteerd. Selecteer eerst een model in de navigatiebalk rechtsboven.</div>
      {/if}
    </div>
    
    <!-- Sectie voor woorden die behouden moeten blijven -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Woorden die niet vereenvoudigd moeten worden
      </label>
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
      
      {#if preservedWords.length > 0}
        <div class="flex flex-wrap gap-2 mt-2">
          {#each preservedWords as word, index}
            <div class="bg-blue-100 text-blue-800 px-2 py-1 rounded-md flex items-center">
              <span>{word}</span>
              <button 
                on:click={() => removePreservedWord(index)}
                class="ml-2 text-blue-600 hover:text-blue-800 focus:outline-none"
              >
                ×
              </button>
            </div>
          {/each}
        </div>
      {:else}
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Geen woorden toegevoegd. Woorden die je hier toevoegt worden niet vereenvoudigd in de vertaling.
        </p>
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
          
          {#if isLoading}
            <!-- Radar scan animatie voor het invoerveld -->
          {/if}
        </div>
      </div>
      
      <!-- Midden: Vertaalknop voor kleine schermen -->
      <div class="md:hidden w-full">
        <button 
          on:click={translateToB1}
          disabled={isLoading || !selectedModels[0]}
          class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50"
        >
          {#if !selectedModels[0]}
            Selecteer eerst een model in de navigatiebalk rechtsboven
          {:else if isLoading}
            <div class="flex items-center justify-center">
              <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Bezig met vertalen...
            </div>
          {:else}
            Vertaal naar {languageLevel}-taalniveau
          {/if}
        </button>
      </div>
      
      <!-- Midden: Vertaalpijl voor grotere schermen -->
      <div class="hidden md:flex flex-col items-center justify-center">
        <button 
          on:click={translateToB1}
          disabled={isLoading || !selectedModels[0]}
          class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-full focus:outline-none focus:shadow-outline disabled:opacity-50 h-12 w-12 flex items-center justify-center"
          title="Vertaal naar {languageLevel}-taalniveau"
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
            <div class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white min-h-[288px] flex items-center justify-center">
            </div>
            <!-- Animaties uitvoerveld -->
            <div class="progress-line absolute inset-x-0 top-0 h-1 pointer-events-none overflow-hidden">
              <div class="line"></div>
            </div>
            <div class="loading-border absolute inset-0 pointer-events-none rounded-md"></div>
          {:else if outputText && showOutput}
            <div 
              id="output"
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white min-h-[288px] max-h-[288px] overflow-y-auto"
              transition:fade={{ duration: 800 }}
            >
              {outputText}
            </div>
            
            <div class="mt-4 flex justify-end">
              <button
                on:click={() => {
                  navigator.clipboard.writeText(outputText)
                    .then(() => {
                      alert('Tekst gekopieerd naar klembord!');
                    })
                    .catch(err => {
                      console.error('Kon niet kopiëren:', err);
                    });
                }}
                class="bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-white font-medium py-1 px-3 rounded focus:outline-none focus:shadow-outline"
              >
                Kopieer naar klembord
              </button>
            </div>
          {:else}
            <div class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-400 min-h-[288px] flex items-center justify-center">
              <p>Hier verschijnt de vereenvoudigde tekst na vertaling</p>
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  /* Alle bestaande stijlen blijven behouden */
  /* Moving border animation */
  .loading-border::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border: 2px solid transparent;
    border-radius: inherit;
    animation: borderAnimation 2s linear infinite;
    pointer-events: none;
  }

  @keyframes borderAnimation {
    0% {
      border-color: transparent;
      border-top-color: #3b82f6;
    }
    25% {
      border-color: transparent;
      border-right-color: #3b82f6;
    }
    50% {
      border-color: transparent;
      border-bottom-color: #3b82f6;
    }
    75% {
      border-color: transparent;
      border-left-color: #3b82f6;
    }
    100% {
      border-color: transparent;
      border-top-color: #3b82f6;
    }
  }

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