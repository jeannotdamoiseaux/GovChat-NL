<script>
  import { createEventDispatcher } from 'svelte';
  
  const dispatch = createEventDispatcher();
  
  function close() {
    dispatch('close');
  }
</script>

<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
  <div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl mx-4">
    <h2 class="text-2xl font-bold mb-4">Welkom bij B1 Taalniveau</h2>
    
    <div class="mb-6">
      <p class="mb-3">B1 is een taalniveau binnen het Europees Referentiekader (ERK). Teksten op B1-niveau zijn:</p>
      <ul class="list-disc pl-5 space-y-2">
        <li>Helder en eenvoudig geschreven</li>
        <li>Geschikt voor mensen met basiskennis van de taal</li>
        <li>Makkelijk te begrijpen voor een breed publiek</li>
      </ul>
      
      <p class="mt-4">Met deze app kunt u controleren of uw teksten voldoen aan het B1-taalniveau en krijgt u suggesties voor verbetering.</p>
    </div>
    
    <button 
      class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
      on:click={close}
    >
      Begrepen
    </button>
  </div>
</div>