<script>
  import InputArea from './InputArea.svelte';
  import OutputArea from './OutputArea.svelte';
  import WordExclusionManager from './WordExclusionManager.svelte';
  import ActionButton from './ActionButton.svelte';

  let inputText = ""; // Tekst van het linker invoerveld
  let outputText = ""; // Vereenvoudigde tekst (uitvoer)
  let excludedWords = []; // Woorden die niet mogen worden vereenvoudigd

  // Functie om de invoer te versimpelen
  function simplifyText() {
    // Eenvoudige logica om tekst te "versimpelen": vervang lange woorden tenzij ze geëxcludeerd zijn
    outputText = inputText
      .split(" ")
      .map(word =>
        excludedWords.includes(word.toLowerCase()) ? word : word.length > 6 ? word.slice(0, 6) + "…" : word
      )
      .join(" ");
  }

  function updateExcludedWords(words) {
    excludedWords = words;
  }
</script>

<div class="grid grid-cols-1 md:grid-cols-3 gap-4 h-full">
  <!-- Invoer -->
  <InputArea bind:value={inputText} />

  <!-- Actieknop -->
  <div class="flex justify-center items-center">
    <ActionButton on:click={simplifyText} label="Versimpel" />
  </div>

  <!-- Resultaat -->
  <OutputArea value={outputText} />

  <!-- Uitsluitingsmanager -->
  <div class="md:col-span-3">
    <WordExclusionManager on:updateExcludedWords={updateExcludedWords} />
  </div>
</div>

<style>
  /* Eventueel extra styling hier */
  .grid {
    height: 100%;
  }
</style>