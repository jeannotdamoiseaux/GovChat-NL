<script>
  import { onMount } from 'svelte';
  import { user, models as modelsStore } from '$lib/stores';
  
  let inputText = '';
  let outputText = '';
  let isLoading = false;
  let selectedModel = '';
  let error = null;
  let models = [];

  // Gebruik de modelsStore om modellen op te halen
  const unsubscribe = modelsStore.subscribe(value => {
    models = value;
    if (models.length > 0 && !selectedModel) {
      // Selecteer standaard het eerste model
      selectedModel = models[0].id;
    }
  });

  onMount(() => {
    // Cleanup subscription when component is destroyed
    return () => {
      unsubscribe();
    };
  });

  async function translateToB1() {
    if (!inputText.trim()) {
      error = "Voer tekst in om te vertalen";
      return;
    }

    if (!selectedModel) {
      error = "Selecteer een model";
      return;
    }

    error = null;
    isLoading = true;

    try {
      // Get the authentication token
      const token = localStorage.getItem('token');
    
      const payload = {
        model: selectedModel,
        messages: [
          {
            role: "system",
            content: "Je bent een expert in het vereenvoudigen van tekst naar B1-taalniveau. B1-taalniveau betekent dat je korte zinnen gebruikt, eenvoudige woorden kiest, en complexe concepten uitlegt in begrijpelijke taal. Vermijd jargon, lange zinnen en moeilijke woorden. Behoud de betekenis van de originele tekst maar maak deze toegankelijk voor mensen met beperkte taalvaardigheid."
          },
          {
            role: "user",
            content: `Vertaal de volgende tekst naar B1-taalniveau: "${inputText}"`
          }
        ],
        temperature: 0.3,
        metadata: {
          user_id: $user?.id || "anonymous",
          session_id: "b1-taalniveau-tool"
        }
      };

      console.log("Request payload:", payload);

      const response = await fetch('http://localhost:8080/api/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` // Add the authentication token
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
    
    <div class="mb-4">
      <label for="model" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Selecteer model
      </label>
      <select 
        id="model"
        bind:value={selectedModel}
        class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
      >
        {#if models.length === 0}
          <option value="">Geen modellen beschikbaar</option>
        {:else}
          {#each models as model}
            <option value={model.id}>{model.name || model.id}</option>
          {/each}
        {/if}
      </select>
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
        disabled={isLoading || models.length === 0}
        class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50"
      >
        {#if models.length === 0}
          Geen modellen beschikbaar
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