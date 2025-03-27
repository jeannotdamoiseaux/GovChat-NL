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
          <div class="flex items-center justify-center">
            <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Bezig met vertalen...
          </div>
        {:else}
          Vertaal naar B1-taalniveau
        {/if}
      </button>
    </div>
    
    <div class="mt-6">
      <label for="output" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        B1-taalniveau tekst
      </label>
      
      <div class="relative">
        {#if isLoading}
          <div class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white min-h-[150px] flex items-center justify-center">
            <p class="text-gray-500 dark:text-gray-400">Tekst wordt omgezet naar B1-taalniveau...</p>
          </div>
          <!-- Oudijzer animaties -->
          <div class="shimmer-border absolute inset-0 pointer-events-none rounded-md"></div>
          <div class="loading-border absolute inset-0 pointer-events-none rounded-md"></div>
          <div class="gradient-border absolute inset-0 pointer-events-none rounded-md"></div>
          <div class="typewriter-container absolute inset-0 flex items-center justify-center pointer-events-none">
            <p class="typewriter">Bezig met vertalen naar B1-taalniveau...</p>
          </div>
          <div class="circle-expand absolute inset-0 flex items-center justify-center pointer-events-none">
            <div class="circle"></div>
          </div>
          <div class="neon-border absolute inset-0 pointer-events-none rounded-md"></div>
          <div class="holographic-border absolute inset-0 pointer-events-none rounded-md"></div>
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
          <div class="progress-line absolute inset-x-0 top-0 h-1 pointer-events-none overflow-hidden">
            <div class="line"></div>
          </div>
          <div class="wave-container absolute inset-0 flex items-center justify-center pointer-events-none">
            <div class="wave-animation">
              <div></div>
              <div></div>
              <div></div>
              <div></div>
              <div></div>
            </div>
          </div>
          <div class="corners-animation absolute inset-0 pointer-events-none rounded-md"></div>
          <div class="dna-container absolute inset-0 flex items-center justify-center pointer-events-none">
            <div class="dna-animation">
              <div class="strand"></div>
              <div class="strand"></div>
              <div class="strand"></div>
              <div class="strand"></div>
              <div class="strand"></div>
              <div class="strand"></div>
              <div class="strand"></div>
              <div class="strand"></div>
            </div>
          </div>
          <div class="language-transform absolute inset-0 flex items-center justify-center pointer-events-none">
            <div class="words">
              <span>Complex</span>
              <span>Moeilijk</span>
              <span>Eenvoudig</span>
              <span>Helder</span>
              <span>B1-niveau</span>
            </div>
          </div>
          <div class="pixel-transition absolute inset-0 pointer-events-none rounded-md overflow-hidden">
            <div class="pixels"></div>
          </div>
          <div class="floating-bubbles absolute inset-0 pointer-events-none overflow-hidden rounded-md">
            <div class="bubble"></div>
            <div class="bubble"></div>
            <div class="bubble"></div>
            <div class="bubble"></div>
            <div class="bubble"></div>
          </div>
          <div class="text-filter absolute inset-0 flex items-center justify-center pointer-events-none">
            <div class="filter-container">
              <div class="complex-text">Complexe tekst</div>
              <div class="filter"></div>
              <div class="simple-text">B1-tekst</div>
            </div>
          </div>
          <div class="radar-scan absolute inset-0 pointer-events-none rounded-md overflow-hidden">
            <div class="radar"></div>
          </div>
          
          
          
          
          
          
          

          
          








        
        {:else if outputText && showOutput}
          <div 
            id="output"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white min-h-[150px]"
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
          <div class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-400 min-h-[150px] flex items-center justify-center">
            <p>Hier verschijnt de vereenvoudigde tekst na vertaling</p>
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>

<style>
  /* Moving border animation */
  .shimmer-border {
  overflow: hidden;
}

.shimmer-border::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: 2px solid #3b82f6;
  border-radius: inherit;
  background: linear-gradient(
    to right,
    rgba(59, 130, 246, 0) 0%,
    rgba(59, 130, 246, 0.5) 50%,
    rgba(59, 130, 246, 0) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { background-position: 100% 0; }
  100% { background-position: -100% 0; }
}

.gradient-border::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: inherit;
  padding: 2px;
  background: linear-gradient(45deg, #3b82f6, #ec4899, #3b82f6);
  background-size: 200% 200%;
  animation: gradient-animation 3s ease infinite;
  -webkit-mask: 
    linear-gradient(#fff 0 0) content-box, 
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
}

@keyframes gradient-animation {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

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

  /* Typewriter animation */
  .typewriter {
  overflow: hidden;
  border-right: 3px solid #3b82f6;
  white-space: nowrap;
  margin: 0 auto;
  letter-spacing: 0.15em;
  animation: typing 3.5s steps(40, end) infinite, blink-caret 0.75s step-end infinite;
}

@keyframes typing {
  0%, 100% { width: 0 }
  50% { width: 100% }
}

@keyframes blink-caret {
  from, to { border-color: transparent }
  50% { border-color: #3b82f6 }
}

/* Circle expand animation */
.circle-expand .circle {
  width: 40px;
  height: 40px;
  background-color: rgba(59, 130, 246, 0.2);
  border-radius: 50%;
  animation: circle-pulse 1.5s ease-out infinite;
}

@keyframes circle-pulse {
  0% {
    transform: scale(0.8);
    opacity: 1;
  }
  100% {
    transform: scale(2);
    opacity: 0;
  }
}

/* Neon border animation */
.neon-border {
  box-shadow: 0 0 5px #3b82f6, 0 0 10px #3b82f6, 0 0 15px #3b82f6;
  animation: neon-pulse 1.5s ease-in-out infinite alternate;
}

@keyframes neon-pulse {
  from {
    box-shadow: 0 0 5px #3b82f6, 0 0 10px #3b82f6, 0 0 15px #3b82f6;
  }
  to {
    box-shadow: 0 0 10px #3b82f6, 0 0 20px #3b82f6, 0 0 30px #3b82f6;
  }
}

.holographic-border::before {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  border: 2px solid transparent;
  border-radius: inherit;
  background: linear-gradient(45deg, 
    #ff0000, #ff7f00, #ffff00, #00ff00, 
    #0000ff, #4b0082, #8b00ff, #ff0000);
  background-size: 400% 400%;
  animation: rainbow 3s linear infinite;
  -webkit-mask: 
    linear-gradient(#fff 0 0) content-box, 
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
}

@keyframes rainbow {
  0% { background-position: 0% 50%; }
  100% { background-position: 100% 50%; }
}

/* 3D shadow animation */
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

/* Progress bar animation */
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

/* Wave animation */
.wave-animation {
  display: flex;
  align-items: center;
  height: 30px;
}

.wave-animation div {
  background: #3b82f6;
  height: 100%;
  width: 5px;
  margin: 0 3px;
  border-radius: 10px;
  animation: wave 1.2s infinite ease-in-out;
}

.wave-animation div:nth-child(2) {
  animation-delay: -1.1s;
}

.wave-animation div:nth-child(3) {
  animation-delay: -1.0s;
}

.wave-animation div:nth-child(4) {
  animation-delay: -0.9s;
}

.wave-animation div:nth-child(5) {
  animation-delay: -0.8s;
}

@keyframes wave {
  0%, 40%, 100% { transform: scaleY(0.4); }
  20% { transform: scaleY(1.0); }
}

/* Corners animation */
.corners-animation::before {
  content: '';
  position: absolute;
  width: 20px;
  height: 20px;
  border-top: 3px solid #3b82f6;
  border-left: 3px solid #3b82f6;
  top: 0;
  left: 0;
  border-radius: 4px 0 0 0;
  animation: corners-rotate 2s linear infinite;
}

.corners-animation::after {
  content: '';
  position: absolute;
  width: 20px;
  height: 20px;
  border-bottom: 3px solid #3b82f6;
  border-right: 3px solid #3b82f6;
  bottom: 0;
  right: 0;
  border-radius: 0 0 4px 0;
  animation: corners-rotate 2s linear infinite;
}

@keyframes corners-rotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* DNA animation */
.dna-animation {
  display: flex;
  height: 50px;
  width: 30px;
  justify-content: space-between;
}

.dna-animation .strand {
  width: 3px;
  height: 100%;
  background-color: #3b82f6;
  border-radius: 3px;
  animation: dna-wave 1.2s infinite ease-in-out;
}

.dna-animation .strand:nth-child(1) { animation-delay: -1.2s; }
.dna-animation .strand:nth-child(2) { animation-delay: -1.1s; }
.dna-animation .strand:nth-child(3) { animation-delay: -1.0s; }
.dna-animation .strand:nth-child(4) { animation-delay: -0.9s; }
.dna-animation .strand:nth-child(5) { animation-delay: -0.8s; }
.dna-animation .strand:nth-child(6) { animation-delay: -0.7s; }
.dna-animation .strand:nth-child(7) { animation-delay: -0.6s; }
.dna-animation .strand:nth-child(8) { animation-delay: -0.5s; }

@keyframes dna-wave {
  0%, 40%, 100% { transform: scaleY(0.4); }
  20% { transform: scaleY(1.0); }
}

/* Language transform animation */
.language-transform .words {
  overflow: hidden;
  height: 30px;
}

.language-transform .words span {
  display: block;
  height: 100%;
  padding-left: 10px;
  color: #3b82f6;
  font-weight: bold;
  animation: language-cycle 5s infinite;
}

@keyframes language-cycle {
  0%, 20% { transform: translateY(0); }
  25%, 45% { transform: translateY(-30px); }
  50%, 70% { transform: translateY(-60px); }
  75%, 95% { transform: translateY(-90px); }
  100% { transform: translateY(-120px); }
}

/* Pixel transition animation */
.pixel-transition {
  background-color: rgba(59, 130, 246, 0.1);
}

.pixel-transition .pixels {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 5px;
  background-color: #3b82f6;
  box-shadow: 0 0 10px 2px rgba(59, 130, 246, 0.5);
  animation: pixel-move 2s infinite;
}

@keyframes pixel-move {
  0% { left: 0; }
  100% { left: 100%; }
}

/* Floating bubbles animation */
.floating-bubbles {
  background-color: rgba(59, 130, 246, 0.05);
}

.floating-bubbles .bubble {
  position: absolute;
  bottom: -20px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: rgba(59, 130, 246, 0.3);
  animation: float 4s infinite ease-in;
}

.floating-bubbles .bubble:nth-child(1) {
  left: 10%;
  animation-duration: 3s;
}

.floating-bubbles .bubble:nth-child(2) {
  left: 30%;
  animation-duration: 5s;
  animation-delay: 1s;
}

.floating-bubbles .bubble:nth-child(3) {
  left: 50%;
  animation-duration: 4s;
  animation-delay: 0.5s;
}

.floating-bubbles .bubble:nth-child(4) {
  left: 70%;
  animation-duration: 6s;
  animation-delay: 2s;
}

.floating-bubbles .bubble:nth-child(5) {
  left: 90%;
  animation-duration: 3.5s;
  animation-delay: 1.5s;
}

@keyframes float {
  0% {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
  100% {
    transform: translateY(-120px) scale(1.5);
    opacity: 0;
  }
}

/* Text filter animation */
.text-filter .filter-container {
  position: relative;
  height: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.text-filter .complex-text {
  font-weight: bold;
  color: #666;
}

.text-filter .filter {
  height: 10px;
  width: 100%;
  margin: 5px 0;
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
  border-radius: 5px;
  position: relative;
  overflow: hidden;
}

.text-filter .filter::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 30px;
  background: rgba(255, 255, 255, 0.7);
  filter: blur(5px);
  animation: filter-light 2s infinite;
}

.text-filter .simple-text {
  font-weight: bold;
  color: #3b82f6;
}

@keyframes filter-light {
  0% { transform: translateX(-30px); }
  100% { transform: translateX(100px); }
}

/* Radar scan animation */
.radar-scan {
  background-color: rgba(59, 130, 246, 0.05);
}

.radar-scan .radar {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 1px;
  height: 1px;
  border-radius: 50%;
  box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.5);
  animation: radar 2s infinite;
}

@keyframes radar {
  0% {
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.5);
  }
  100% {
    box-shadow: 0 0 0 200px rgba(59, 130, 246, 0);
  }
}












</style>