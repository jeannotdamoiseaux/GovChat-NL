<script>
  import { onMount, getContext } from 'svelte';
  import { user, models as modelsStore, settings } from '$lib/stores';
  import { WEBUI_BASE_URL } from '$lib/constants';
  import { fade } from 'svelte/transition';
  import { toast } from 'svelte-sonner';
  import { updateUserSettings } from '$lib/apis/users';
  
  const i18n = getContext('i18n');
  
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
  let languageLevel = 'B1';
  
  // Standaard uitgesloten woorden - deze moeten overeenkomen met de lijst in de backend
  const defaultPreservedWords = [
    "pancreaskopcarcinoom", 
    "DigiD", 
    "MijnOverheid", 
    "BSN", 
    "Burgerservicenummer",
    "WOZ", 
    "IBAN", 
    "BIC", 
    "KvK", 
    "BTW", 
    "BRP", 
    "UWV", 
    "SVB", 
    "DUO", 
    "CAK", 
    "CJIB"
  ];
  
  // Nieuwe state variabele om bij te houden of de standaard lijst gebruikt moet worden
  let useDefaultPreservedWords = true;
  
  // Functie om modellen op te halen
  async function fetchModels() {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${WEBUI_BASE_URL}/api/models`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      modelsStore.set(data.data);
      return data.data;
    } catch (error) {
      console.error("Error fetching models:", error);
      toast.error(`Fout bij het ophalen van modellen: ${error.message || "Onbekende fout"}`);
      throw error;
    }
  }
  
  // Functie om het geselecteerde model op te slaan in gebruikersinstellingen
  const saveDefaultModel = async () => {
    const hasEmptyModel = selectedModels.filter((it) => it === '');
    if (hasEmptyModel.length) {
      toast.error($i18n ? $i18n.t('Choose a model before saving...') : 'Kies eerst een model...');
      return;
    }
    
    // Sla het model op in de b1TranslatorModel property van de settings
    settings.set({ ...$settings, b1TranslatorModel: selectedModels[0] });
    await updateUserSettings(localStorage.token, { ui: $settings });

    toast.success($i18n ? $i18n.t('Default model updated') : 'Standaard model bijgewerkt');
  };
  
  // Functie om het geselecteerde model te herstellen uit gebruikersinstellingen
  function restoreSelectedModel() {
    // Als er een opgeslagen model is in de settings en het bestaat in de beschikbare modellen
    if ($settings?.b1TranslatorModel && models.some(m => m.id === $settings.b1TranslatorModel)) {
      selectedModels = [$settings.b1TranslatorModel];
      return true;
    } 
    // Als er geen opgeslagen model is of het bestaat niet meer, gebruik het eerste beschikbare model
    else if (models.length > 0) {
      selectedModels = [models[0].id];
      return true;
    }
    return false;
  }
  
  // Gebruik de modelsStore om modellen op te halen
  const unsubscribe = modelsStore.subscribe(value => {
    models = value;
    
    // Als er modellen zijn, probeer het geselecteerde model te herstellen
    if (models.length > 0) {
      restoreSelectedModel();
    }
  });

  onMount(async () => {
    await fetchModels();
    
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
        language_level: languageLevel,
        use_default_preserved_words: useDefaultPreservedWords // Geef door of de standaard lijst gebruikt moet worden
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

<!-- Voeg een container toe met margin-top om het component naar beneden te verplaatsen -->
<div class="max-w-7xl mx-auto mt-20">
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
        <!-- Voeg een knop toe om het model op te slaan als standaard -->
        <button 
          on:click={saveDefaultModel}
          class="text-xs text-blue-600 dark:text-blue-400 hover:underline mt-1"
        >
          {$i18n ? $i18n.t('Set as default') : 'Instellen als standaard'}
        </button>
      {:else}
        <div class="font-medium text-yellow-600">Geen model geselecteerd. Selecteer eerst een model in de navigatiebalk rechtsboven.</div>
      {/if}
    </div>
    
    <!-- Sectie voor woorden die behouden moeten blijven -->
    <div class="mb-4">
      <div class="flex justify-between items-center mb-2">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Woorden die niet vereenvoudigd moeten worden
        </label>
      </div>
      
      <!-- Optie om standaard uitgesloten woorden te gebruiken -->
      <div class="mb-3 flex items-center">
        <input 
          type="checkbox" 
          id="useDefaultWords" 
          bind:checked={useDefaultPreservedWords}
          class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        >
        <label for="useDefaultWords" class="ml-2 block text-sm text-gray-700 dark:text-gray-300">
          Gebruik standaard uitgesloten woorden
        </label>
      </div>
      
      <!-- Toon standaard uitgesloten woorden als de optie is ingeschakeld -->
      {#if useDefaultPreservedWords}
        <div class="mb-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-md border border-gray-200 dark:border-gray-600">
          <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Standaard uitgesloten woorden:</h3>
          <div class="flex flex-wrap gap-2">
            {#each defaultPreservedWords as word}
              <div class="bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-200 px-2 py-1 rounded-md text-xs">
                {word}
              </div>
            {/each}
          </div>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">
            Deze woorden worden automatisch behouden in de vertaling.
          </p>
        </div>
      {/if}
      
      <div class="flex mb-2">
        <input
          type="text"
          bind:value={newPreservedWord}
          placeholder="Voer een extra woord of term in"
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
          Geen extra woorden toegevoegd. Je kunt hier aanvullende woorden toevoegen die niet vereenvoudigd moeten worden.
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
            <div class="cube-container absolute inset-0 flex items-center justify-center pointer-events-none">
              <div class="cube">
                <div class="side front"></div>
                <div class="side back"></div>
                <div class="side top"></div>
                <div class="side bottom"></div>
                <div class="side left"></div>
                <div class="side right"></div>
              </div>
            </div>
            
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

.cube {
  width: 40px;
  height: 40px;
  position: relative;
  transform-style: preserve-3d;
  animation: cube-rotate 3s infinite linear;
}

.cube .side {
  position: absolute;
  width: 100%;
  height: 100%;
  background: rgba(59, 130, 246, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.cube .front { transform: translateZ(20px); }
.cube .back { transform: rotateY(180deg) translateZ(20px); }
.cube .top { transform: rotateX(90deg) translateZ(20px); }
.cube .bottom { transform: rotateX(-90deg) translateZ(20px); }
.cube .left { transform: rotateY(-90deg) translateZ(20px); }
.cube .right { transform: rotateY(90deg) translateZ(20px); }

@keyframes cube-rotate {
  0% { transform: rotateX(0) rotateY(0); }
  100% { transform: rotateX(360deg) rotateY(360deg); }
}
</style>
          