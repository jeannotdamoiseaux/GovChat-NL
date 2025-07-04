<script>
  import { onMount } from 'svelte'; 
  import { models, settings } from '$lib/stores';
  import { filteredModels, currentAppContext } from '$lib/stores/appModels';
  import { WEBUI_BASE_URL } from '$lib/constants';
  import { fade } from 'svelte/transition';
  import { toast } from 'svelte-sonner';
  import Modal from '$lib/components/common/Modal.svelte';
  import { browser } from '$app/environment';
  
  // Modal control variables
  let showPreservedWordsModal = false;
  let showInfoModal = false;

  let inputText = '';
  let outputText = '';
  let isLoading = false;
  let error = null;
  let newPreservedWord = '';
  let showOutput = false;
  let languageLevel = 'B1';

  let useDefaultWords = true;

  const originalDefaultWords = [
    'Provinciale Staten', 'Gedeputeerde Staten', 'Directieteam', 'Regulier overleg (RO)',
    'Fracties', 'Statenleden', 'Statenlid', 'Gedeputeerde', 'Commissaris van de Koning (CdK)',
    'Subsidie', 'Begroting', 'Interprovinciaal overleg (IPO)', 'Ruimtelijke ordening',
    'Regionaal beleid', 'Provinciefonds', 'Omgevingsvisie', 'Provinciale verordening',
    'Regionaal samenwerkingsverband', 'Gebiedscommissie', 'Waterplan', 'Milieubeleidsplan',
    'Inpassingsplan', 'Ruimtelijk Economisch Programma', 'Uitvoeringsprogramma Bereikbaarheid',
    'Adaptatieplan Klimaat', 'Erfgoedprogramma', 'Interprovinciaal Coördinatie Overleg (IPCO)',
    'Regionaal Beleidsplan Verkeersveiligheid (RBV)', 'Regionaal economisch beleid',
    'Ontwikkelingsfonds', 'Veiligheids- en Crisismanagementplan (RVCP)', 'Natuurbeheer',
    'Waterbeheer', 'Milieubeleid', 'Mobiliteitsbeleid', 'Plattelandsontwikkeling',
    'Provinciale infrastructuur', 'Omgevingsverordening', 'Energietransitie', 'Waterkwaliteit',
    'Duurzaamheidsagenda', 'Natuurbeheerplan', 'Mobiliteitsvisie', 'Sociale agenda',
    'Bodembeleid', 'Burgerparticipatie', 'Ecologie', 'Ecologisch', 'Groenbeleid',
    'Natuur- en landschapsbeheerorganisaties', 'Informerend stuk', 'Onderwerp', 'Samenvatting', 
    'Kennisnemen van', 'Aanleiding en bestuurlijke context', 'Bevoegdheid', 'Communicatie', 'Vervolg', 
    'Bijlage(n)', 'Sonderend stuk', 'Vraag aan PS', 'Context', 'Voorstel', 'Statenvoorstel', 'Geachte', 'Argumenten'
  ];

  let activeDefaultWords = [...originalDefaultWords];
  let userWords = [];
  let initialLoadComplete = false;

  // Reactive statement for preservedWords based on user words and default toggle
  $: preservedWords = useDefaultWords ? [...new Set([...userWords, ...activeDefaultWords])] : [...new Set(userWords)];

  // Helper function to get current model from sessionStorage
  function getCurrentModel() {
    if (!browser) return '';
    try {
      const stored = sessionStorage.getItem('selectedModels');
      if (stored) {
        const parsed = JSON.parse(stored);
        return Array.isArray(parsed) && parsed.length > 0 ? parsed[0] : '';
      }
    } catch (e) {
      console.error('Error parsing selectedModels from sessionStorage:', e);
    }
    return '';
  }

  // Helper function to set model in sessionStorage
  function setCurrentModel(modelId) {
    if (browser) {
      sessionStorage.setItem('selectedModels', JSON.stringify([modelId]));
    }
  }

  onMount(async () => {
    // Set app context to B1 to ensure proper model filtering
    currentAppContext.set('b1');
    
    if (browser) {
      // Load user preserved words
      const storedUserWords = localStorage.getItem('b1UserPreservedWords');
      if (storedUserWords) {
        try {
          const parsedWords = JSON.parse(storedUserWords);
          if (Array.isArray(parsedWords)) {
            userWords = parsedWords;
          }
        } catch (e) {
          console.error('Error parsing userWords from localStorage:', e);
        }
      }
      
      // Set initial model if none exists
      if (!getCurrentModel() && $settings?.models && $settings.models.length > 0) {
        setCurrentModel($settings.models[0]);
      }
      
      // Show info modal on first visit
      if (!localStorage.getItem('b1TutorialShown')) {
        showInfoModal = true;
        localStorage.setItem('b1TutorialShown', 'true');
      }
      
      initialLoadComplete = true;
    }
  });

  // Save userWords to localStorage whenever it changes
  $: if (browser && initialLoadComplete) {
    localStorage.setItem('b1UserPreservedWords', JSON.stringify(userWords));
  }

  // Ensure a valid model is selected when models are loaded
  $: if (browser && $models && $models.length > 0) {
    const currentModel = getCurrentModel();
    const allModelIds = $models.map(m => m.id);
    
    if (currentModel && !allModelIds.includes(currentModel)) {
      // Invalid model, find a replacement
      const validModel = $filteredModels && $filteredModels.length > 0 
        ? $filteredModels[0].id 
        : allModelIds[0];
      if (validModel) setCurrentModel(validModel);
    } else if (!currentModel && allModelIds.length > 0) {
      // No model selected, set a default
      const defaultModel = $filteredModels && $filteredModels.length > 0 
        ? $filteredModels[0].id 
        : allModelIds[0];
      if (defaultModel) setCurrentModel(defaultModel);
    }
  }

  // Word counting and progress variables
  let wordCountPercentage = 0;
  let inputWordCount = 0;
  let outputWordCount = 0;

  function countWords(text) {
    if (!text) return 0;
    return text.trim().split(/\s+/).filter(word => word.length > 0).length;
  }

  $: inputWordCount = countWords(inputText);

  // Chunk processing variables
  let chunkResults = [];
  let totalChunks = 0;
  let receivedChunks = 0;

  const MAX_WORDS = 24750; // Define the word limit

  // Main function to trigger text simplification
  async function simplifyText() {
    // Reset errors and state
    error = null;
    isLoading = true;
    outputText = '';
    chunkResults = [];
    totalChunks = 0;
    receivedChunks = 0;
    outputWordCount = 0;
    wordCountPercentage = 0;
    showOutput = true; // Show output area immediately

    // --- Input Validations ---
    if (!inputText.trim()) {
      error = "Voer tekst in om te vereenvoudigen";
      toast.error(error);
      isLoading = false;
      showOutput = false;
      return;
    }

    if (inputWordCount > MAX_WORDS) {
      error = `De invoertekst (${inputWordCount} woorden) overschrijdt de limiet van ${MAX_WORDS} woorden.`;
      toast.error(error);
      isLoading = false;
      showOutput = false; // Don't show output area if input is invalid
      return;
    }

    const currentModel = getCurrentModel();
    if (!currentModel) {
      error = "Selecteer eerst een model";
      toast.error(error);
      isLoading = false;
      showOutput = false;
      return;
    }

    // Validate model availability and use fallback if needed
    let modelToUse = currentModel;
    const allModelIds = $models?.map(m => m.id) || [];
    const b1ModelIds = $filteredModels?.map(m => m.id) || [];
    
    if (b1ModelIds.length > 0 && !b1ModelIds.includes(currentModel)) {
      modelToUse = b1ModelIds[0];
    } else if (allModelIds.length > 0 && !allModelIds.includes(currentModel)) {
      modelToUse = allModelIds[0];
    }
    
    if (modelToUse !== currentModel) {
      setCurrentModel(modelToUse);
    }
    // --- End Validations ---


    try {
      const response = await fetch(`${WEBUI_BASE_URL}/api/b1/translate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          text: inputText,
          model: modelToUse, // Using the validated model (original or fallback)
          preserved_words: preservedWords, 
          language_level: languageLevel
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error("Response body is missing");
      }

      // Process the streaming response
      const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += value;
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep the potentially incomplete last line

        for (const line of lines) {
          if (line.trim() === '') continue;

          try {
            const parsed = JSON.parse(line);

            if (parsed.total_chunks !== undefined) {
              totalChunks = parsed.total_chunks;
              // Initialize results array only if totalChunks > 0
              chunkResults = totalChunks > 0 ? Array(totalChunks).fill('') : [];
            } else if (parsed.index !== undefined && parsed.text !== undefined) {
              if (parsed.index >= 0 && parsed.index < totalChunks) {
                chunkResults[parsed.index] = parsed.text;
                receivedChunks++;

                // Update output text by joining received chunks
                outputText = chunkResults.map(chunk => chunk ?? '').join('\n'); // Use ?? for nullish coalescing

                // Update progress
                wordCountPercentage = totalChunks > 0 ? Math.round((receivedChunks / totalChunks) * 100) : 0;
              } else {
                 console.warn("Received chunk with out-of-bounds index:", parsed);
              }
            }
          } catch (e) {
            console.error("Error parsing streamed JSON line:", e, "Line:", line);
            // Optionally show a user-facing error or handle differently
          }
        }
      }

      // Final update after stream ends
      outputText = chunkResults.map(chunk => chunk ?? '').join('\n');
      outputWordCount = countWords(outputText);
      wordCountPercentage = 100; // Ensure 100% at the end

    } catch (err) {
      console.error('Error simplifying text:', err);
      const errorMessage = err instanceof Error ? err.message : 'Onbekende fout';
      error = `Fout: ${errorMessage}`;
      toast.error(`Fout bij vereenvoudigen: ${errorMessage}`);
      showOutput = false;
    } finally {
      isLoading = false;
      // Final progress state adjustments
      if (!error && totalChunks > 0) {
          wordCountPercentage = 100;
          receivedChunks = totalChunks;
      } else if (error) {
          wordCountPercentage = 0;
      } else if (totalChunks === 0 && !error) {
          wordCountPercentage = 100;
          outputText = inputText;
          outputWordCount = countWords(outputText);
      }
    }
  }

  function addPreservedWord() {
    const wordToAdd = newPreservedWord.trim();
    if (wordToAdd) {
      if (!userWords.includes(wordToAdd)) {
          userWords = [...userWords, wordToAdd];
      }
      newPreservedWord = '';
    }
  }

  function removePreservedWord(wordToRemove) {
    userWords = userWords.filter(w => w !== wordToRemove);
    activeDefaultWords = activeDefaultWords.filter(w => w !== wordToRemove);
  }

  // Reset activeDefaultWords when the toggle is turned on
  $: if (useDefaultWords) {
    activeDefaultWords = [...originalDefaultWords];
  }

  // File handling variables
  let fileInput;
  let isProcessingFile = false;
  let isFlashing = false;
  let fileProcessingProgress = 0;
  let fileProcessingInterval = null;

  // Handle drag & drop files
  function handleFileDrop(event) {
    const file = event.dataTransfer?.files?.[0];
    if (!file) return;

    if (!file.name.match(/\.(doc|docx|pdf|txt|rtf)$/i)) {
      toast.error('Alleen Word, PDF, TXT of RTF bestanden zijn toegestaan');
      return;
    }

    // Process the dropped file directly
    processDroppedFile(file);
  }

  // Process dropped file without going through the file input
  async function processDroppedFile(file) {
    // Start progress simulation
    isProcessingFile = true;
    isFlashing = true;
    fileProcessingProgress = 0;
    if (fileProcessingInterval) clearInterval(fileProcessingInterval);

    fileProcessingInterval = setInterval(() => {
      if (fileProcessingProgress < 99) {
        fileProcessingProgress += 1;
        if (fileProcessingProgress > 98) {
          fileProcessingProgress = 99;
        }
      } else {
        clearInterval(fileProcessingInterval);
        fileProcessingInterval = null;
      }
    }, 50);

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
         inputText = uploadData.content;
      } else if (uploadData.id) {
          const contentResponse = await fetch(`${WEBUI_BASE_URL}/api/v1/files/${uploadData.id}/data/content`, {
              headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
          });
          if (!contentResponse.ok) {
              throw new Error('Fout bij ophalen bestandsinhoud na upload');
          }
          const textData = await contentResponse.json();
          inputText = textData.content;
      } else {
          throw new Error('Onbekend antwoordformaat van upload endpoint');
      }

      // Convert HTML strong tags to markdown for docx files
      if (file.name.match(/\.(doc|docx)$/i)) {
        inputText = inputText.replace(/<strong>(.*?)<\/strong>/gi, '**$1**');
      }

      toast.success('Bestand succesvol verwerkt');

    } catch (err) {
      console.error('Error processing file:', err);
      const errorMessage = err instanceof Error ? err.message : 'Onbekende fout';
      toast.error(`Fout bij verwerken bestand: ${errorMessage}`);
      inputText = '';
    } finally {
      if (fileProcessingInterval) {
        clearInterval(fileProcessingInterval);
        fileProcessingInterval = null;
      }
      fileProcessingProgress = 100;
      isProcessingFile = false;
      setTimeout(() => isFlashing = false, 1000);
    }
  }

  // File upload handler using /api/v1/files
  async function handleFileUpload(event) {
    const file = event.target?.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.name.match(/\.(doc|docx|pdf|txt|rtf)$/i)) {
      toast.error('Alleen Word, PDF, TXT of RTF bestanden zijn toegestaan');
      return;
    }

    // Use the same processing function as drag & drop
    await processDroppedFile(file);
    
    // Reset file input
    if (fileInput) fileInput.value = '';
  }

  function processText(text) {
    if (!text) return '';
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  }

  // Reactive calculation for progress display text
  $: progressDisplay = totalChunks > 0 ? Math.round((receivedChunks / totalChunks) * 100) : (isLoading ? 0 : (outputText ? 100 : 0));

</script>
<div class="max-w-7xl mx-auto mt-6">
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
    <div class="flex justify-between items-center mb-6">
      <div class="flex items-start gap-2">
        <div>
          <h1 class="text-2xl font-bold text-gray-800 dark:text-white">
            Versimpelaar
          </h1>
          <p class="text-lg text-gray-600 dark:text-gray-300">
            Kies een tekst en breng die eenvoudig naar B1- of B2-niveau.
          </p>
          <button
            on:click={() => showInfoModal = true}
            class="bg-blue-100 hover:bg-blue-200 dark:bg-blue-700 dark:hover:bg-blue-600 text-blue-700 dark:text-blue-200 font-medium py-1.5 px-3 rounded-md focus:outline-none focus:shadow-outline flex items-center gap-1.5 mb-1"
            aria-label="Uitleg over de Versimpelaar"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Wat doet de Versimpelaar?</span>
          </button>
        </div>
      </div>
      
      <!-- Taalniveau dropdown -->
      <div class="flex items-center">
        <label for="language-level-select" class="mr-2 text-sm text-gray-600 dark:text-gray-400">Taalniveau:</label>
        <select 
          id="language-level-select"
          bind:value={languageLevel}
          class="px-3 py-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white text-sm"
        >
          <option value="B1">B1</option>
          <option value="B2">B2</option>
        </select>
      </div>
    </div>
    
    {#if error}
      <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4" transition:fade>
        {error}
      </div>
    {/if}
    
    <!-- Replace existing preserved words section - removed button -->
    <div class="mb-4">
      <!-- Removed the flex justify-between and the button -->
      <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Begrippen die je wilt behouden:
      </h3>
      
      <!-- Preview of preserved words (first 5 with count) -->
      {#if preservedWords.length > 0}
        <div class="text-sm text-gray-600 dark:text-gray-400">
          <div class="flex flex-wrap gap-1">
            {#each preservedWords.slice(0, 5) as word}
              <!-- Keep clickable words to open modal -->
              <span 
                class="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 px-2 py-0.5 rounded-md cursor-pointer hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors"
                on:click={() => showPreservedWordsModal = true}
                role="button"
              >
                {word}
              </span>
            {/each}
            {#if preservedWords.length > 5}
              <span 
                class="text-gray-500 dark:text-gray-400 px-2 py-0.5 cursor-pointer hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
                on:click={() => showPreservedWordsModal = true}
                role="button"
              >
                +{preservedWords.length - 5} extra begrippen...
              </span>
            {/if}
          </div>
        </div>
      {:else}
        <div 
          class="text-sm text-gray-600 dark:text-gray-400 italic cursor-pointer hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
          on:click={() => showPreservedWordsModal = true}
          role="button"
        >
          Geen woorden geselecteerd
        </div>
      {/if}
    </div>
    
    <!-- Flex container voor input en output naast elkaar -->
    <div class="flex flex-col md:flex-row gap-6">
      <!-- Linker kolom: Input -->
      <div class="flex-1 flex flex-col">
        <label for="input" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Oorspronkelijke tekst
        </label>
        <div class="relative flex flex-col h-full flex-grow">
          <!-- Textarea with consistent height -->
          <textarea
            id="input"
            bind:value={inputText}
            rows="12"
            draggable="false"
            class="w-full h-[400px] flex-grow px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white min-h-[250px] md:min-h-[400px] overflow-y-auto font-[system-ui] {isFlashing ? 'flash-animation' : ''}"
            placeholder="Plak of typ hier de tekst die je wilt vereenvoudigen."
            disabled={isLoading}
            spellcheck="false"
            on:dragover|preventDefault
            on:drop|preventDefault={handleFileDrop}
          ></textarea>

          <!-- Bottom section with fixed height and spacing -->
          <div class="mt-auto">
            <!-- Progress bar - same position as right side -->
            <div class="mt-2 flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <div class="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  class="bg-blue-600 h-2 rounded-full transition-all duration-200"
                  style="width: {isProcessingFile ? fileProcessingProgress : (fileProcessingProgress === 100 ? 100 : 0)}%"
                ></div>
              </div>
              <span class="min-w-[4rem] text-right">
                {isProcessingFile ? fileProcessingProgress : (fileProcessingProgress === 100 ? 100 : 0)}%
              </span>
            </div>

            <!-- Status text - fixed height -->
            <div class="mt-1 h-5 text-xs text-gray-500 dark:text-gray-400">
              {#if isProcessingFile}
                <span>Verwerken...</span>
              {:else if fileProcessingProgress === 100}
                <span>Bestand verwerkt</span>
              {:else}
                <span>of sleep bestand naar invoerveld (Word, PDF, TXT, RTF)</span>
              {/if}
            </div>

            <!-- Button row - exactly same structure as right side -->
            <div class="mt-1 flex justify-between pb-2">
              <input
                type="file"
                id="fileInput"
                class="hidden"
                bind:this={fileInput}
                accept=".doc,.docx,.pdf,.txt,.rtf"
                on:change={handleFileUpload}
              />
              
              <button
                on:click={() => fileInput.click()}
                disabled={isProcessingFile}
                class="bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-white font-medium py-1 px-3 rounded focus:outline-none focus:shadow-outline disabled:opacity-50 min-w-[140px] flex items-center justify-center gap-2"
              >
                {#if isProcessingFile}
                  <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Verwerken...</span>
                {:else if !isProcessingFile && fileProcessingProgress === 100}
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Bestand verwerkt</span>
                {:else}
                  <span>Document uploaden</span>
                {/if}
              </button>
              
              <!-- Empty div to match the structure of right side -->
              <div></div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Midden: Translate button -->
      <div class="hidden md:flex flex-col items-center justify-center">
        <button
          on:click={simplifyText}
          disabled={isLoading || !getCurrentModel()}
          class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-full focus:outline-none focus:shadow-outline disabled:opacity-50 h-12 w-12 flex items-center justify-center"
          title="Versimpel naar {languageLevel}-taalniveau"
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

      <!-- Rechter kolom: Output - IDENTICAL dimensions to left column -->
      <div class="flex-1 flex flex-col">
        <label for="output" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Vereenvoudigde tekst
        </label>
        <div class="relative flex flex-col h-full flex-grow">
          <!-- Output with EXACT same height as input -->
          {#if showOutput}
            <div
              id="output"
              class="w-full h-[400px] flex-grow px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white min-h-[250px] md:min-h-[400px] overflow-y-auto whitespace-pre-wrap font-[system-ui]"
              transition:fade={{ duration: 200 }}
            >
              {@html processText(outputText)}
            </div>
          {:else if !isLoading}
            <div class="w-full h-[400px] flex-grow px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-400 min-h-[250px] md:min-h-[400px] flex items-center justify-center">
              <p>Hier zie je straks de vereenvoudigde tekst.</p>
            </div>
          {/if}

          <!-- Bottom section with fixed height and spacing -->
          <div class="mt-auto">
            <!-- Progress bar - same position as left side -->
            <div class="mt-2 flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
              <div class="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  class="bg-blue-600 h-2 rounded-full transition-all duration-200"
                  style="width: {wordCountPercentage}%"
                ></div>
              </div>
              <span class="min-w-[4rem] text-right">
                {progressDisplay}%
              </span>
            </div>

            <!-- Status text - fixed height -->
            <div class="mt-1 h-5 text-xs text-gray-500 dark:text-gray-400">
              {#if isLoading}
                <span>Paragrafen verwerkt: {receivedChunks} / {totalChunks || '?'}</span>
              {:else if outputText}
                <span>Woorden: {outputWordCount} (Origineel: {inputWordCount})</span>
              {:else}
                <span>Klaar om te verwerken</span>
              {/if}
            </div>

            <!-- Button row - exactly same structure as left side -->
            <div class="mt-1 flex justify-between pb-2">
              <!-- Empty div to match the structure of left side -->
              <div></div>
              
              <button
                on:click={() => {
                  navigator.clipboard.writeText(outputText);
                  toast.success('Tekst gekopieerd!');
                }}
                disabled={!outputText}
                class="bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-white font-medium py-1 px-3 rounded focus:outline-none focus:shadow-outline disabled:opacity-50 min-w-[140px] flex items-center justify-center"
              >
                Kopieer tekst
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Modal for preserved words management -->
<Modal
  bind:show={showPreservedWordsModal}
  size="md"
  containerClassName="p-0"
>
  <div class="p-6">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-bold text-gray-800 dark:text-white">
        Geef aan welke woorden je niet wilt vereenvoudigen.
      </h2>
      <button
        on:click={() => showPreservedWordsModal = false}
        class="text-gray-400 hover:text-gray-500 focus:outline-none"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
    
    <!-- Input field to add new words -->
    <div class="flex mb-4">
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

    <!-- Toggle for default words -->
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
        Standaard te behouden woorden (Bodembeleid, Subsidie, etc.)
      </span>
    </div>

    <!-- List of preserved words -->
    <div class="max-h-[300px] overflow-y-auto border border-gray-300 rounded-md p-3 bg-gray-50 dark:bg-gray-700 dark:border-gray-600 space-y-4">
      <!-- User-added words -->
      <div>
        <h4 class="text-sm font-semibold text-gray-600 dark:text-gray-300 mb-2">
          Door Gebruiker Toegevoegde Woorden
        </h4>
        {#if userWords.length > 0}
          <div class="flex flex-wrap gap-2">
            {#each userWords as word (word)}
              <div class="bg-green-100 text-green-800 dark:bg-green-700 dark:text-green-100 px-2.5 py-1 rounded-md flex items-center text-sm">
                <span>{word}</span>
                <button
                  on:click={() => removePreservedWord(word)}
                  class="ml-2 text-green-600 hover:text-green-800 dark:text-green-300 dark:hover:text-green-100 focus:outline-none"
                  title="Verwijder dit woord"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            {/each}
          </div>
        {:else}
          <p class="text-sm text-gray-500 dark:text-gray-400 italic">Geen eigen woorden toegevoegd.</p>
        {/if}
      </div>

      <!-- Default words (if toggle is on) -->
      {#if useDefaultWords}
        <div>
          <h4 class="text-sm font-semibold text-gray-600 dark:text-gray-300 mb-2">
            Standaard Woorden (actief)
          </h4>
          {#if activeDefaultWords.length > 0}
            <div class="flex flex-wrap gap-2">
              {#each activeDefaultWords as word (word)}
                <div class="bg-blue-100 text-blue-800 dark:bg-blue-700 dark:text-blue-100 px-2.5 py-1 rounded-md flex items-center text-sm">
                  <span>{word}</span>
                  <button
                    on:click={() => removePreservedWord(word)}
                    class="ml-2 text-blue-600 hover:text-blue-800 dark:text-blue-300 dark:hover:text-blue-100 focus:outline-none"
                    title="Verberg dit standaard woord tijdelijk (wordt hersteld als de toggle uit/aan gaat)"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              {/each}
            </div>
          {:else}
             <p class="text-sm text-gray-500 dark:text-gray-400 italic">Alle standaard woorden zijn momenteel verborgen. Zet de toggle hierboven uit en weer aan om ze te herstellen.</p>
          {/if}
        </div>
      {/if}

      {#if userWords.length === 0 && (!useDefaultWords || activeDefaultWords.length === 0)}
        <div class="text-center text-gray-500 dark:text-gray-400 py-4">
          Geen woorden geselecteerd om te behouden. Voeg eigen woorden toe of activeer de standaardlijst via de toggle hierboven.
        </div>
      {/if}
    </div>

    <div class="mt-6 flex justify-end">
      <button
        on:click={() => showPreservedWordsModal = false}
        class="bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-white font-medium py-1 px-3 rounded focus:outline-none focus:shadow-outline"
      >
        Sluiten
      </button>
    </div>
  </div>
</Modal>

<!-- New modal for app information -->
<Modal
  bind:show={showInfoModal}
  size="md"
  containerClassName="p-0"
>
  <div class="p-6">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-bold text-gray-800 dark:text-white">
        Over de Versimpelaar
      </h2>
      <button
        on:click={() => showInfoModal = false}
        class="text-gray-400 hover:text-gray-500 focus:outline-none"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
    
    <div class="space-y-4 text-gray-700 dark:text-gray-300">
      <p>
        De Versimpelaar ondersteunt je bij het omzetten van complexe teksten naar eenvoudige taal op B1- of B2-niveau. Hierdoor worden teksten beter leesbaar en begrijpelijk voor een groter publiek.
      </p>
      <h3 class="text-lg font-medium text-gray-800 dark:text-white mt-4">Wat is B1-taalniveau?</h3>
      <p>
        B1 is een niveau binnen het Europees Referentiekader (ERK) voor talen. Teksten op B1-niveau:
      </p>
      <ul class="list-disc pl-5 space-y-1">
        <li>Gebruiken eenvoudige en veelvoorkomende woorden;</li>
        <li>Bevatten korte zinnen (doorgaans 15 tot 20 woorden per zin);</li>
        <li>Vermijden ingewikkelde zinsconstructies en vakjargon;</li>
        <li>Zijn concreet, duidelijk en direct geformuleerd.</li>
      <p>
        B1-niveau is geschikt voor de meeste volwassenen in Nederland, ook voor mensen met een lagere taalvaardigheid.
      </p>
      </ul>
      <h3 class="text-lg font-medium text-gray-800 dark:text-white mt-4">
      Hoe gebruik je de Versimpelaar?
      </h3>
      <ol class="list-decimal pl-5 space-y-1">
        <li>
          <strong>Voer een tekst in</strong><br>
          Plak de tekst die je wilt vereenvoudigen in het linkervak. Je kunt ook een document (Word, PDF, TXT, RTF) uploaden of rechtstreeks in het vak slepen.
        </li>
        <li>
          <strong>Kies termen om te behouden (optioneel)</strong><br>
          Selecteer specifieke woorden of termen die niet vereenvoudigd mogen worden. Er is standaard een lijst toegevoegd met veelgebruikte provinciale begrippen. Je kunt deze lijst aanvullen of aanpassen.
        </li>
        <li>
          <strong>Start de verwerking</strong><br>
          Klik op de pijl tussen het linker- en rechtervak om de tekst om te zetten.
        </li>
        <li>
          <strong>Bekijk en gebruik de vereenvoudigde tekst</strong><br>
          De Versimpelaar toont de vereenvoudigde tekst in het rechtervak. Je kunt deze vervolgens kopiëren en verder gebruiken.
        </li>
      </ol>
      <p class="mt-3 text-sm text-orange-700 dark:text-orange-300 font-semibold">
        <strong>Let op:</strong><br>
        De Versimpelaar is een hulpmiddel. Controleer altijd zelf de uitkomst en pas deze waar nodig aan.
      </p>
    </div>
    <div class="mt-6 flex justify-end">
      <button
        on:click={() => showInfoModal = false}
        class="bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-white font-medium py-1 px-3 rounded focus:outline-none focus:shadow-outline"
      >
        Sluiten
      </button>
    </div>
  </div>
</Modal>

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
  
  /* Output strong elements */
  :global(#output strong) {
    font-weight: 700;
    color: inherit;
  }

  /* Flash animation */
  @keyframes flash {
    0% {
      background-color: rgba(59, 130, 246, 0);
      transform: scale(1);
      box-shadow: 0 0 0 0 rgba(96, 165, 250, 0);
    }
    15% {
      background-color: rgba(59, 130, 246, 0.2);
      transform: scale(1.02);
      box-shadow: 0 0 30px 15px rgba(96, 165, 250, 0.3),
                 0 0 0 30px rgba(96, 165, 250, 0.1),
                 inset 0 0 15px rgba(255, 255, 255, 0.4);
    }
    30% {
      background-color: rgba(59, 130, 246, 0.1);
      transform: scale(1);
      box-shadow: 0 0 50px 20px rgba(96, 165, 250, 0.1),
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

  /* Optional: Style for the progress text during loading */
  .progress-text {
    font-variant-numeric: tabular-nums; /* Keeps numbers aligned */
  }
</style>