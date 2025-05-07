<script>
  import { onMount, getContext } from 'svelte'; 
  import { models, settings } from '$lib/stores';
  import { WEBUI_BASE_URL } from '$lib/constants';
  import { fade } from 'svelte/transition';
  import { toast } from 'svelte-sonner';
  import Modal from '$lib/components/common/Modal.svelte';
  
  // Add modal control variables
  let showPreservedWordsModal = false;
  let showInfoModal = false; // New variable for info modal

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
    'Natuur- en landschapsbeheerorganisaties'
  ];

  let activeDefaultWords = [...originalDefaultWords];
  let userWords = [];

  // Reactive statement for preservedWords based on user words and default toggle
  $: preservedWords = useDefaultWords ? [...new Set([...userWords, ...activeDefaultWords])] : [...new Set(userWords)]; // Use Set to ensure uniqueness

  // Model selection logic
  let selectedModels = ['']; 
  $: availableModels = $models || [];

  onMount(async () => {
    // Load model selection from settings or local storage
    const storedModels = $settings?.models?.length > 0 ? $settings.models : null;
    const storedModelLegacy = localStorage.getItem('selectedModel'); // Check legacy single model storage

    if (storedModels) {
      selectedModels = storedModels;
    } else if (storedModelLegacy) {
       selectedModels = [storedModelLegacy]; // Convert legacy storage to array
       localStorage.removeItem('selectedModel'); // Clean up legacy item
       // Optionally save the new array format back to settings/localStorage
       settings.update(s => ({ ...s, models: selectedModels }));
       localStorage.setItem('selectedModels', JSON.stringify(selectedModels)); // Example using new key
    } else {
      // Fallback to first available model if no selection stored
      selectedModels = availableModels.length ? [availableModels[0].id] : [''];
    }
  });

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

    const currentModel = selectedModels[0]; // Get the currently selected model
    if (!currentModel) {
      error = "Selecteer eerst een model";
      toast.error(error);
      isLoading = false;
      showOutput = false;
      return;
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
          model: currentModel, // Use the validated model
          preserved_words: preservedWords, // Use the reactive preservedWords
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
      error = `Fout: ${err.message}`;
      toast.error(`Fout bij vereenvoudigen: ${err.message}`);
      showOutput = false; // Hide output on error
    } finally {
      isLoading = false;
      // Final progress state adjustments
      if (!error && totalChunks > 0) {
          wordCountPercentage = 100;
          receivedChunks = totalChunks; // Ensure counter matches total
      } else if (error) {
          wordCountPercentage = 0; // Reset progress on error
      } else if (totalChunks === 0 && !error) {
          // Handle case where input resulted in zero chunks (e.g., only whitespace)
          wordCountPercentage = 100;
          outputText = inputText; // Or keep outputText empty? Decide desired behavior.
          outputWordCount = countWords(outputText);
      }
    }
  }

  // Function to add a word to the user's preserved list
  function addPreservedWord() {
    const wordToAdd = newPreservedWord.trim();
    if (wordToAdd) {
      // Avoid adding duplicates directly to userWords
      if (!userWords.includes(wordToAdd)) {
          userWords = [...userWords, wordToAdd];
      }
      newPreservedWord = ''; // Clear input field
    }
  }

  // Function to remove a word from preserved lists
  function removePreservedWord(wordToRemove) {
    // Remove from user list if present
    userWords = userWords.filter(w => w !== wordToRemove);
    // Remove from active default list if present (allows temporarily disabling a default word)
    activeDefaultWords = activeDefaultWords.filter(w => w !== wordToRemove);
  }

  // Reactive effect to reset activeDefaultWords when the toggle is turned on
  $: if (useDefaultWords) {
    // Ensure activeDefaultWords contains all original defaults not explicitly removed by the user
    // This logic might need refinement depending on desired behavior when toggling off/on
     activeDefaultWords = [...originalDefaultWords]; // Simple reset for now
  } else {
    // Optionally clear activeDefaultWords when toggled off, or leave as is
    // activeDefaultWords = [];
  }

  // File handling variables
  let fileInput; // Reference to the file input element
  let isProcessingFile = false;
  let isFlashing = false; // For visual feedback on drop/upload
  let fileProcessingProgress = 0; // State for fake progress
  let fileProcessingInterval = null; // Interval timer reference

  // Updated file upload handler using /api/v1/files
  async function handleFileUpload(event) {
    const file = event.target?.files?.[0]; // Use optional chaining
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
    if (fileProcessingInterval) clearInterval(fileProcessingInterval); // Clear previous interval if any

    fileProcessingInterval = setInterval(() => {
      if (fileProcessingProgress < 99) {
        fileProcessingProgress += 1; // Increment by 2% each time
        if (fileProcessingProgress > 98) {
          // Slow down near the end to simulate waiting for processing // Stop at 99%
          fileProcessingProgress = 99;
        }
      } else {
        clearInterval(fileProcessingInterval);
        fileProcessingInterval = null;
      }
    }, 50); // Update every 50ms for smoother feel (adjust as needed)
    // --- End Fake Progress Start ---


    try {
      const formData = new FormData();
      formData.append('file', file);
      // The 'type' might not be needed depending on the backend /api/v1/files implementation
      // formData.append('type', 'document');

      // Call the standard file upload endpoint
      const uploadResponse = await fetch(`${WEBUI_BASE_URL}/api/v1/files`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
          // Content-Type is set automatically by browser for FormData
        },
        body: formData
      });

      if (!uploadResponse.ok) {
        const errorData = await uploadResponse.json().catch(() => ({ detail: 'Fout bij uploaden bestand' }));
        throw new Error(errorData.detail || 'Fout bij uploaden bestand');
      }

      const uploadData = await uploadResponse.json();

      // Assuming the upload endpoint returns the extracted text or an ID to fetch it
      // The previous code fetched content separately, adjust based on actual /api/v1/files response
      if (uploadData.content) { // If content is directly in response
         inputText = uploadData.content;
      } else if (uploadData.id) { // If an ID is returned, fetch content
          const contentResponse = await fetch(`${WEBUI_BASE_URL}/api/v1/files/${uploadData.id}/data/content`, {
              method: 'GET',
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


      // Convert strong tags from potential backend processing back to markdown **
      // This depends on whether the /api/v1/files endpoint returns HTML or plain text
      // Assuming it might return HTML with <strong> for bold from docx
      if (file.name.match(/\.(doc|docx)$/i)) {
        // Be cautious with replace, ensure it doesn't break intended markdown
        inputText = inputText.replace(/<strong>(.*?)<\/strong>/gi, '**$1**');
      }

      toast.success('Bestand succesvol verwerkt');

    } catch (err) {
      console.error('Error processing file:', err);
      toast.error(`Fout bij verwerken bestand: ${err.message}`);
      inputText = ''; // Clear input on error
    } finally {
      // --- Stop Fake Progress ---
      if (fileProcessingInterval) clearInterval(fileProcessingInterval); // Clear interval if still running
      fileProcessingInterval = null;
      fileProcessingProgress = 100; // Set to 100% on completion (success or error)
      isProcessingFile = false; // Set processing to false *after* setting progress to 100
      // --- End Fake Progress Stop ---

      if (fileInput) fileInput.value = ''; // Reset file input
      // End visual feedback after a short delay
      setTimeout(() => {
        isFlashing = false;
        // Optionally reset progress visual after flash animation
        // setTimeout(() => { fileProcessingProgress = 0; }, 500); // Reset after another delay if needed
      }, 1000);
    }
  }

  // Helper function to convert markdown **bold** to HTML <strong> for display
  function processText(text) {
    if (!text) return '';
    // Replace **text** with <strong>text</strong>, handle spaces around **
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  }

  // Reactive calculation for progress display text
  $: progressDisplay = totalChunks > 0 ? Math.round((receivedChunks / totalChunks) * 100) : (isLoading ? 0 : (outputText ? 100 : 0));

</script>
<div class="max-w-7xl mx-auto mt-6">
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
    <div class="flex justify-between items-center mb-6">
      <div class="flex items-center gap-2">
        <h1 class="text-2xl font-bold text-gray-800 dark:text-white">
          {languageLevel}-Taalniveau Vereenvoudiger
        </h1>
        <!-- Add info button next to the title -->
        <button
          on:click={() => showInfoModal = true}
          class="bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-white font-medium py-1 px-2 rounded-full focus:outline-none focus:shadow-outline flex items-center justify-center w-6 h-6"
          aria-label="Informatie over de B1-taalniveau app"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </button>
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
    
    <!-- Replace existing preserved words section with a button to open modal -->
    <div class="mb-4">
      <div class="flex justify-between items-center">
        <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300">
          Woorden die niet vereenvoudigd mogen worden:
        </h3>
        <button
          on:click={() => showPreservedWordsModal = true}
          class="bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-white font-medium py-1 px-3 rounded focus:outline-none focus:shadow-outline"
        >
          Beheer woorden ({preservedWords.length})
        </button>
      </div>
      
      <!-- Preview of preserved words (first 5 with count) -->
      {#if preservedWords.length > 0}
        <div class="mt-2 text-sm text-gray-600 dark:text-gray-400">
          <div class="flex flex-wrap gap-1">
            {#each preservedWords.slice(0, 5) as word}
              <span class="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 px-2 py-0.5 rounded-md">
                {word}
              </span>
            {/each}
            {#if preservedWords.length > 5}
              <span class="text-gray-500 dark:text-gray-400 px-2 py-0.5">
                +{preservedWords.length - 5} meer...
              </span>
            {/if}
          </div>
        </div>
      {:else}
        <div class="mt-2 text-sm text-gray-600 dark:text-gray-400 italic">
          Geen woorden geselecteerd
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
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white min-h-[250px] md:min-h-[400px] max-h-[250px] md:max-h-[400px] overflow-y-auto font-[system-ui] {isFlashing ? 'flash-animation' : ''}"
            placeholder="Voer hier de tekst in die je wilt vereenvoudigen naar {languageLevel}-taalniveau."
            disabled={isLoading}
            spellcheck="false"
            on:dragover|preventDefault
            on:drop|preventDefault={(event) => {
              const file = event.dataTransfer.files[0];
              if (file) {
                if (file.name.match(/\.(doc|docx|pdf|txt|rtf)$/i)) {
                  handleFileUpload({ target: { files: [file] } });
                } else {
                  toast.error('Alleen Word, PDF, TXT of RTF bestanden zijn toegestaan');
                }
              }
            }}
          ></textarea>

          <!-- Container for controls/info below input textarea -->
          <div class="mt-2">
            <!-- File Upload Progress - Always visible -->
            <div class="flex items-center gap-2">
              <!-- Progress Bar Container -->
              <div class="flex-grow bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  class="bg-blue-600 h-2 rounded-full transition-all duration-150 ease-linear"
                  style="width: {isProcessingFile ? fileProcessingProgress : (fileProcessingProgress === 100 ? 100 : 0)}%"
                ></div>
              </div>
              <!-- Percentage Text -->
              <span class="text-sm text-gray-600 dark:text-gray-400 min-w-[3rem] text-right">
                {isProcessingFile ? fileProcessingProgress : (fileProcessingProgress === 100 ? 100 : 0)}%
              </span>
            </div>

            <!-- Upload knop en drag & drop hint -->
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
                  on:click={() => fileInput.click()}
                  disabled={isProcessingFile}
                  class="bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-white font-medium py-1 px-3 rounded focus:outline-none focus:shadow-outline disabled:opacity-50 flex items-center gap-2"
                >
                  {#if isProcessingFile}
                    <!-- Show spinner while processing -->
                    <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Verwerken...</span>
                  {:else if !isProcessingFile && fileProcessingProgress === 100}
                    <!-- Show checkmark when done -->
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    </svg>
                    <span>Bestand verwerkt</span>
                  {:else}
                    <!-- Default upload icon -->
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3 3m0 0l-3-3m3 3V8" />
                    </svg>
                    <span>Upload document</span>
                  {/if}
                </button>
              </div>
              <span class="text-sm text-gray-500 dark:text-gray-400 text-right">
                of sleep bestand naar invoerveld<br>(Word, PDF, TXT, RTF)
              </span>
            </div>
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
          <!-- Output content area - conditional display -->
          {#if showOutput}
            <div 
              id="output"
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white min-h-[250px] md:min-h-[400px] max-h-[250px] md:max-h-[400px] overflow-y-auto whitespace-pre-wrap font-[system-ui]"
              transition:fade={{ duration: 200 }}
            >
              {@html processText(outputText)}
            </div>
          {:else if !isLoading}
            <div class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-400 min-h-[250px] md:min-h-[400px] flex items-center justify-center">
              <p>Hier verschijnt de vereenvoudigde tekst na verwerking</p>
            </div>
          {/if}
          
          <!-- Progress bar - ALWAYS visible -->
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
          
          <!-- Status text - ALWAYS visible -->
          <div class="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {#if isLoading}
              Paragrafen verwerkt: {receivedChunks} / {totalChunks || '?'}
            {:else if outputText}
              Woorden: {outputWordCount} (Origineel: {inputWordCount})
            {:else}
              Klaar om te verwerken
            {/if}
          </div>
          
          <!-- Kopieer knop - Always visible but disabled when no content -->
          <div class="mt-1 flex justify-end">
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
              disabled={!outputText}
              class="bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-white font-medium py-1 px-3 rounded focus:outline-none focus:shadow-outline disabled:opacity-50"
            >
              Kopieer naar klembord
            </button>
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
        Woorden die niet vereenvoudigd worden
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
        Standaard niet te veranderen woorden (Bodembeleid, Subsidie, etc.)
      </span>
    </div>
    
    <!-- List of preserved words -->
    <div class="max-h-[300px] overflow-y-auto border border-gray-300 rounded-md p-2 bg-gray-50 dark:bg-gray-700 dark:border-gray-600">
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
      
      {#if preservedWords.length === 0}
        <div class="text-center text-gray-500 dark:text-gray-400 py-4">
          Geen woorden geselecteerd. Voeg woorden toe die niet vereenvoudigd mogen worden.
        </div>
      {/if}
    </div>
    
    <div class="mt-4 flex justify-end">
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
        Over de B1-taalniveau Vereenvoudiger
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
        De B1-taalniveau Vereenvoudiger helpt je om complexe teksten naar eenvoudigere taal om te zetten, zodat ze beter te begrijpen zijn voor een breder publiek.
      </p>
      
      <h3 class="text-lg font-medium text-gray-800 dark:text-white mt-4">Wat is B1-taalniveau?</h3>
      <p>
        B1-taalniveau is een taalvaardigheidsniveau volgens het Europees Referentiekader (ERK). Teksten op B1-niveau:
      </p>
      <ul class="list-disc pl-5 space-y-1">
        <li>Gebruiken eenvoudige, alledaagse woorden</li>
        <li>Hebben kortere zinnen (15-20 woorden per zin)</li>
        <li>Vermijden moeilijke zinsconstructies en jargon</li>
        <li>Zijn concreet en direct</li>
      </ul>
      
      <h3 class="text-lg font-medium text-gray-800 dark:text-white mt-4">Hoe werkt het?</h3>
      <ol class="list-decimal pl-5 space-y-1">
        <li>Voer je tekst in of upload een document (Word, PDF, TXT of RTF)</li>
        <li>Kies welke woorden niet vereenvoudigd mogen worden (optioneel)</li>
        <li>Klik op de "Vereenvoudig" knop</li>
        <li>De AI zal je tekst omzetten naar B1-taalniveau</li>
      </ol>
      
      <h3 class="text-lg font-medium text-gray-800 dark:text-white mt-4">Tips voor betere resultaten</h3>
      <ul class="list-disc pl-5 space-y-1">
        <li>Voeg vaktermen en organisatienamen toe aan "Woorden die niet vereenvoudigd worden"</li>
        <li>Controleer de vereenvoudigde tekst altijd op juistheid</li>
        <li>Voor langere teksten kun je beter stukken apart invoeren</li>
      </ul>
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
  
  /* Progress line animation */

  
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

  /* Optional: Style for the progress text during loading */
  .progress-text {
     font-variant-numeric: tabular-nums; /* Keeps numbers aligned */
  }
</style>
