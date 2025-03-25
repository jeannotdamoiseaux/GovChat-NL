<script>
  import { onMount } from 'svelte';
  import { user, models as modelsStore } from '$lib/stores';
  import { WEBUI_BASE_URL } from '$lib/constants';
  
  // Props - ontvang selectedModels van de parent component
  export let selectedModels = [''];
  
  let inputText = '';
  let outputText = '';
  let isLoading = false;
  let error = null;
  let preservedWords = []; 
  let newPreservedWord = '';
  let models = [];
  
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

  async function translateToB1() {
    if (!inputText.trim()) {
      error = "Voer tekst in om te vertalen";
      return;
    }

    // Controleer of er een model is geselecteerd
    if (!selectedModels[0]) {
      error = "Selecteer eerst een model in de navigatiebalk rechtsboven";
      return;
    }

    error = null;
    isLoading = true;

    try {
      // Get the authentication token
      const token = localStorage.getItem('token');
      
      // Maak een payload voor de backend API
      const payload = {
        model: selectedModels[0],
        text: inputText,
        preserved_words: preservedWords
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
    } catch (err) {
      console.error("Error translating:", err);
      error = "Fout bij vertalen: " + (err.message || "Onbekende fout");
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="max-w-4xl mx-auto">
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
    <h1 class="text-2xl font-bold mb-6 text-gray-800 dark:text-white">B1-Taalniveau Vertaler</h1>
    
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
    
    <div class="mb-4">
      <label for="input" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Originele tekst
      </label>
      <textarea
        id="input"
        bind:value={inputText}
        rows="6"
        class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
        placeholder="Voer hier de tekst in die je wilt vereenvoudigen naar B1-taalniveau..."
      ></textarea>
    </div>
    
    <div class="mb-4">
      <button 
        on:click={translateToB1}
        disabled={isLoading || !selectedModels[0]}
        class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50"
      >
        {#if !selectedModels[0]}
          Selecteer eerst een model in de navigatiebalk rechtsboven
        {:else if isLoading}
          Bezig met vertalen...
        {:else}
          Vertaal naar B1-taalniveau
        {/if}
      </button>
    </div>
    
    {#if outputText}
      <div class="mt-6">
        <label for="output" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          B1-taalniveau tekst
        </label>
        <div 
          id="output"
          class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white min-h-[150px]"
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
      </div>
    {/if}
  </div>
</div>