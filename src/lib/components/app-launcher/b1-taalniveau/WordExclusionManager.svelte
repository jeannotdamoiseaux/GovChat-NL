<script>
  import { createEventDispatcher } from 'svelte';

  let words = ""; // Gegeven lijst met uitgesloten woorden
  const dispatch = createEventDispatcher();

  function updateWords() {
    const wordList = words.split(",").map(word => word.trim().toLowerCase());
    dispatch("updateExcludedWords", wordList);
  }
</script>

<div class="mt-4">
  <label class="block text-gray-700">Uitsluit woorden (komma-gescheiden):</label>
  <input
    type="text"
    class="w-full p-2 border rounded"
    placeholder="Bijv.: gedeputeerde, subsidie"
    bind:value={words}
  />
  <button
    class="mt-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 shadow transition"
    on:click={updateWords}
  >
    Update Uitsluitingen
  </button>
</div>