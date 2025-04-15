<script>
  import { onMount, getContext } from 'svelte';
  import { models, settings } from '$lib/stores';
  import { WEBUI_BASE_URL } from '$lib/constants';
  import { fade } from 'svelte/transition';
  import { toast } from 'svelte-sonner';
  import { createOpenAITextStream } from '$lib/apis/streaming';

  const i18n = getContext('i18n');

  let inputText = '';
  let outputText = '';
  let isLoading = false;
  let error = null;
  let preservedWords = [];
  let newPreservedWord = '';
  let showOutput = false;
  let languageLevel = 'B1';
  
  let useDefaultWords = true;

  // Vervang de defaultWords met deze twee constanten
  const originalDefaultWords = [
    'Provinciale Staten',
    'Gedeputeerde Staten',
    'Directieteam',
    'Regulier overleg (RO)',
    'Fracties',
    'Statenleden',
    'Statenlid',
    'Gedeputeerde',
    'Commissaris van de Koning (CdK)',
    'Subsidie',
    'Begroting',
    'Interprovinciaal overleg (IPO)',
    'Ruimtelijke ordening',
    'Regionaal beleid',
    'Provinciefonds',
    'Omgevingsvisie',
    'Provinciale verordening',
    'Regionaal samenwerkingsverband',
    'Gebiedscommissie',
    'Waterplan',
    'Milieubeleidsplan',
    'Inpassingsplan',
    'Ruimtelijk Economisch Programma',
    'Uitvoeringsprogramma Bereikbaarheid',
    'Adaptatieplan Klimaat',
    'Erfgoedprogramma',
    'Interprovinciaal Coördinatie Overleg (IPCO)',
    'Regionaal Beleidsplan Verkeersveiligheid (RBV)',
    'Regionaal economisch beleid',
    'Ontwikkelingsfonds',
    'Veiligheids- en Crisismanagementplan (RVCP)',
    'Natuurbeheer',
    'Waterbeheer',
    'Milieubeleid',
    'Mobiliteitsbeleid',
    'Plattelandsontwikkeling',
    'Provinciale infrastructuur',
    'Omgevingsverordening',
    'Energietransitie',
    'Waterkwaliteit',
    'Duurzaamheidsagenda',
    'Natuurbeheerplan',
    'Mobiliteitsvisie',
    'Sociale agenda',
    'Bodembeleid',
    'Burgerparticipatie',
    'Ecologie',
    'Ecologisch',
    'Groenbeleid',
    'Natuur- en landschapsbeheerorganisaties'
  ];

  let activeDefaultWords = [...originalDefaultWords];
  let userWords = [];

  // Wijzig het reactive statement
  $: preservedWords = useDefaultWords ? [...userWords, ...activeDefaultWords] : userWords;

  // Change single model to array of models like in chat
  let selectedModels = [''];
  let selectedModel = ''; // Keep this for compatibility
  
  $: availableModels = $models || [];
  $: selectedModel = selectedModels[0] || ''; // Sync selectedModel with first model in array

  onMount(async () => {
    // Get model selection from settings or localStorage
    if ($settings?.models?.length > 0) {
      selectedModels = $settings.models;
      selectedModel = selectedModels[0];
    } else {
      const storedModel = localStorage.getItem('selectedModel');
      selectedModels = storedModel ? [storedModel] : availableModels.length ? [availableModels[0].id] : [''];
      selectedModel = selectedModels[0];
    }
  });

  // Update model selection function
  function saveModelSelection(modelId) {
    selectedModels = [modelId]; // Keep as array for consistency with chat
    selectedModel = modelId;
    localStorage.setItem('selectedModel', modelId);
    
    // Update settings if needed
    if ($settings) {
      settings.update(s => ({
        ...s,
        models: selectedModels
      }));
    }
  }

  let wordCountPercentage = 0;
  let inputWordCount = 0;
  let outputWordCount = 0;

  function countWords(text) {
    return text.trim().split(/\s+/).filter(word => word.length > 0).length;
  }

  $: inputWordCount = countWords(inputText);

  async function simplifyText() {
    try {
      if (!inputText.trim()) {
        error = "Voer tekst in om te vereenvoudigen";
        return;
      }

      if (!selectedModels[0]) {
        error = "Selecteer eerst een model";
        return;
      }

      isLoading = true;
      error = null;
      outputText = '';
      outputWordCount = 0;
      wordCountPercentage = 0;
      showOutput = true;

      const response = await fetch(`${WEBUI_BASE_URL}/api/b1/translate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          text: inputText,
          model: selectedModels[0],
          preserved_words: preservedWords,
          language_level: languageLevel
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Use the same streaming approach as chat
      const stream = await createOpenAITextStream(response.body);
      
      for await (const chunk of stream) {
        if (chunk.error) {
          throw new Error(chunk.error);
        }
        if (!chunk.done) {
          outputText += chunk.value;
          outputWordCount = countWords(outputText);
          wordCountPercentage = Math.round((outputWordCount / inputWordCount) * 100);
        } else {
          // Als de stream klaar is, zet percentage op 100%
          wordCountPercentage = 100;
        }
      }

    } catch (err) {
      console.error('Error simplifying text:', err);
      error = `Error: ${err.message}`;
      toast.error('Error simplifying text');
    } finally {
      isLoading = false;
      // Extra check om zeker te zijn dat het 100% is na voltooiing
      if (showOutput && outputText) {
        wordCountPercentage = 100;
      }
    }
  }

  // Functie om een woord toe te voegen aan de lijst van te behouden woorden
  function addPreservedWord() {
    if (newPreservedWord.trim()) {
      userWords = [...userWords, newPreservedWord.trim()];
      newPreservedWord = '';
    }
  }

  // Wijzig de removePreservedWord functie
  function removePreservedWord(word) {
    if (originalDefaultWords.includes(word)) {
      // Als het een standaardwoord is, verwijder het uit activeDefaultWords
      activeDefaultWords = activeDefaultWords.filter(w => w !== word);
    } else {
      // Als het een gebruikerswoord is
      userWords = userWords.filter(w => w !== word);
    }
  }

  // Functie om te schakelen tussen B1 en B2 taalniveau
  function toggleLanguageLevel() {
    languageLevel = languageLevel === 'B1' ? 'B2' : 'B1';
  }

  // Voeg deze watch toe voor useDefaultWords
  $: if (useDefaultWords) {
    // Als de switch wordt aangezet, reset de activeDefaultWords naar origineel
    activeDefaultWords = [...originalDefaultWords];
  }

  // Voeg deze variabelen toe
  let fileInput;
  let isProcessingFile = false;
  let isFlashing = false;

  // Vervang de handleFileUpload functie met deze versie
  async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
  
    // Check bestandstype
    if (!file.name.match(/\.(doc|docx)$/i)) {
      toast.error('Alleen Word documenten (.doc of .docx) zijn toegestaan');
      return;
    }
  
    isProcessingFile = true;
    isFlashing = true; // Start de flash animatie
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`${WEBUI_BASE_URL}/api/b1/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });
  
      if (!response.ok) throw new Error('Fout bij uploaden bestand');
      
      const data = await response.json();
      // Zet dikgedrukte tekst om naar markdown formaat
      inputText = data.text.replace(/<strong>(.*?)<\/strong>/g, '**$1**');
      toast.success('Bestand succesvol geüpload');
    } catch (err) {
      console.error('Error uploading file:', err);
      toast.error('Fout bij verwerken bestand');
    } finally {
      isProcessingFile = false;
      if (fileInput) fileInput.value = ''; // Reset input
      // Reset de flash animatie na een korte vertraging
      setTimeout(() => {
        isFlashing = false;
      }, 1000);
    }
  }
  
  // Voeg deze helper functie toe voor tekst verwerking
  function processText(text) {
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  }
</script>
<div class="max-w-7xl mx-auto mt-9">
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
      
      <!-- Vervang de tags container div met deze aangepaste versie -->
      <div class="max-h-29 overflow-y-auto border border-gray-300 rounded-md p-2 bg-gray-50 dark:bg-gray-700 dark:border-gray-600">
        <div class="flex flex-wrap gap-2">
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
    </div>

    <!-- Knop om standaard woorden toe te voegen -->
    <div class="mb-4 flex items-center gap-2">
      <div class="flex items-center">
        <button 
          type="button"
          class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 {useDefaultWords ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-600'}"
          role="switch"
          aria-checked={useDefaultWords}
          on:click={() => useDefaultWords = !useDefaultWords}
        >
          <span 
            class="translate-x-0 pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out {useDefaultWords ? 'translate-x-5' : 'translate-x-0'}"
          />
        </button>
      </div>
      <span class="text-sm text-gray-700 dark:text-gray-300">
        Standaard niet te veranderen woorden (Bodembeleid, Subsidie, etc.)
      </span>
    </div>
    
    <!-- Flex container voor input en output naast elkaar -->
    <div class="flex flex-col md:flex-row gap-6">
      <!-- Linker kolom: Input -->
      <div class="flex-1">
        <label for="input" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Originele tekst
        </label>
        <div class="relative"
          on:dragover|preventDefault
          on:drop|preventDefault={(event) => {
            const file = event.dataTransfer.files[0];
            if (file) {
              if (file.name.match(/\.(doc|docx)$/i)) {
                handleFileUpload({ target: { files: [file] } });
              } else {
                toast.error('Alleen Word documenten (.doc of .docx) zijn toegestaan');
              }
            }
          }}
        >
          <textarea
            id="input"
            bind:value={inputText}
            rows="12"
            draggable="false"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white min-h-[250px] md:min-h-[400px] max-h-[250px] md:max-h-[400px] overflow-y-auto font-[system-ui] {isFlashing ? 'flash-animation' : ''}"
            placeholder="Voer hier de tekst in die je wilt vereenvoudigen naar {languageLevel}-taalniveau... Gebruik ** voor dikgedrukte tekst"
            disabled={isLoading}
            spellcheck="false"
          ></textarea>

          <!-- Upload knop en drag & drop hint onder textarea -->
          <div class="mt-2 flex items-center gap-2">
            <input
              type="file"
              accept=".doc,.docx"
              class="hidden"
              bind:this={fileInput}
              on:change={handleFileUpload}
            />
            <button
              on:click={() => fileInput.click()}
              disabled={isProcessingFile}
              class="bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-white font-medium py-1 px-3 rounded focus:outline-none focus:shadow-outline flex items-center gap-2"
            >
              {#if isProcessingFile}
                <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              {:else}
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3 3m0 0l-3-3m3 3V8" />
                </svg>
              {/if}
              Upload Word document
            </button>
            <span class="text-sm text-gray-500 dark:text-gray-400">
              of sleep een Word bestand hierheen
            </span>
          </div>
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
              <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 24 24">
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
          
          <!-- Vervang de Output sectie met deze nieuwe structuur -->
          {#if showOutput}
            <div 
              id="output"
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white min-h-[250px] md:min-h-[400px] max-h-[250px] md:max-h-[400px] overflow-y-auto whitespace-pre-wrap font-[system-ui]"
              transition:fade={{ duration: 200 }}
            >
              {@html processText(outputText)}
            </div>
            
            <!-- Progress bar direct onder output -->
            {#if isLoading || showOutput}
              <div class="mt-2 flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                <div class="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    class="bg-blue-600 h-2 rounded-full transition-all duration-200"
                    style="width: {wordCountPercentage}%"
                  ></div>
                </div>
                <span class="min-w-[4rem] text-right">
                  {wordCountPercentage}%
                </span>
              </div>
              <div class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Woorden: {outputWordCount} / {inputWordCount}
              </div>
            {/if}
            
            <!-- Kopieer knop onder progress bar -->
            <div class="mt--1 flex justify-end">
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
            <div class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-400 min-h-[250px] md:min-h-[400px] flex items-center justify-center">
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

  :global(#output strong) {
    font-weight: 700;
    color: inherit;
  }

  /*flash animation*/
  @keyframes flash {
    0% {
      background-color: rgba(59, 130, 246, 0);
      transform: scale(1);
      box-shadow: 0 0 0 0 rgba(96, 165, 250, 0);
    }
    15% {
      background-color: rgba(59, 130, 246, 0.2);
      transform: scale(1.02);
      box-shadow: 
        0 0 30px 15px rgba(96, 165, 250, 0.3),
        0 0 0 30px rgba(96, 165, 250, 0.1),
        inset 0 0 15px rgba(255, 255, 255, 0.4);
    }
    30% {
      background-color: rgba(59, 130, 246, 0.1);
      transform: scale(1);
      box-shadow: 
        0 0 50px 20px rgba(96, 165, 250, 0.1),
        0 0 0 40px rgba(96, 165, 250, 0),
        inset 0 0 20px rgba(255, 255, 255, 0.2);
    }
    100% {
      background-color: rgba(59, 130, 246, 0);
      transform: scale(1);
      box-shadow: 0 0 0 0 rgba(96, 165, 250, 0);
    }
  }

  :global(.flash-animation) {
    animation: flash 1.0s cubic-bezier(0.4, 0, 0.2, 1);
    border-color: rgba(96, 165, 250, 0.8);
    position: relative;
  }
</style>
