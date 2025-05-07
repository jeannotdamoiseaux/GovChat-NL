<script>
  import { onMount } from 'svelte';
  import { models, settings } from '$lib/stores';
  import { WEBUI_BASE_URL } from '$lib/constants';
  import { toast } from 'svelte-sonner';

  let inputText = '';
  let outputText = '';
  let isLoading = false;
  let error = null;
  let showOutput = false;
  let languageLevel = 'B1';
  let selectedModel = '';
  let fileInput;
  let isProcessingFile = false;
  let fileProcessingProgress = 0;
  let fileProgressDone = false;
  let fileProcessingInterval = null;
  let isFlashing = false;
  let outputProgressFinal = false;

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

  let useDefaultWords = true;
  let activeDefaultWords = [...originalDefaultWords];
  let userWords = [];
  let newPreservedWord = '';
  $: preservedWords = useDefaultWords
    ? [...new Set([...userWords, ...activeDefaultWords])]
    : [...new Set(userWords)];
  $: availableModels = $models || [];
  onMount(() => {
    if (selectedModel) return;
    const storedModels = $settings?.models?.length > 0 ? $settings.models : null;
    if (storedModels?.length) {
      selectedModel = storedModels[0];
    } else {
      selectedModel = availableModels.length ? availableModels[0].id : '';
    }
  });
  $: if (!selectedModel && availableModels.length) selectedModel = availableModels[0].id;
  $: if (selectedModel && !availableModels.find(m => m.id === selectedModel) && availableModels.length) selectedModel = availableModels[0].id;

  function countWords(txt) {
    return txt ? txt.trim().split(/\s+/).filter(w => w.length > 0).length : 0;
  }
  $: inputWordCount = countWords(inputText);
  $: outputWordCount = countWords(outputText);

  let chunkResults = [];
  let totalChunks = 0;
  let receivedChunks = 0;
  const MAX_WORDS = 24750;
  $: outputProgress = totalChunks > 0 ? Math.round((receivedChunks / totalChunks) * 100) : (isLoading ? 0 : (outputText ? 100 : 0));
  $: if (outputProgress === 100 && isLoading === false) outputProgressFinal = true;
  $: if (isLoading) outputProgressFinal = false;

  // Drag & drop
  let dragActive = false;
  function handleDrag(e) {
    e.preventDefault();
    e.stopPropagation();
    dragActive = e.type === 'dragover' || e.type === 'dragenter';
  }
  async function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    dragActive = false;
    const file = e.dataTransfer?.files?.[0];
    if (file) processFileUpload(file);
  }
  async function handleFileInputChange(e) {
    const file = e.target?.files?.[0];
    if (file) processFileUpload(file);
    if (fileInput) fileInput.value = '';
  }
  async function processFileUpload(file) {
    if (!file) return;
    if (!file.name.match(/\.(doc|docx|pdf|txt|rtf)$/i)) {
      toast.error('Alleen Word, PDF, TXT of RTF toegestaan'); return;
    }
    isProcessingFile = true; isFlashing = true; fileProcessingProgress = 0; fileProgressDone = false;
    if (fileProcessingInterval) clearInterval(fileProcessingInterval);
    fileProcessingInterval = setInterval(() => {
      if (fileProcessingProgress < 97) fileProcessingProgress += 3;
      else clearInterval(fileProcessingInterval);
    }, 35);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const uploadResponse = await fetch(`${WEBUI_BASE_URL}/api/v1/files`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
        body: formData
      });
      if (!uploadResponse.ok) {
        const errorData = await uploadResponse.json().catch(() => ({ detail: 'Fout bij upload' }));
        throw new Error(errorData.detail || 'Fout bij upload bestand');
      }
      const uploadData = await uploadResponse.json();
      if (uploadData.content) { inputText = uploadData.content; }
      else if (uploadData.id) {
        const contentResponse = await fetch(`${WEBUI_BASE_URL}/api/v1/files/${uploadData.id}/data/content`, {
          method: 'GET',
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (!contentResponse.ok) throw new Error('Fout bij ophalen bestand');
        const textData = await contentResponse.json();
        inputText = textData.content;
      } else {
        throw new Error('Onbekend antwoordformaat van upload endpoint');
      }
      if (file.name.match(/\.(doc|docx)$/i)) {
        inputText = inputText.replace(/<strong>(.*?)<\/strong>/gi, '**$1**');
      }
      toast.success('Bestand verwerkt');
      fileProgressDone = true;
    } catch (err) {
      toast.error(`Fout bestand: ${err.message}`);
      inputText = '';
      fileProgressDone = false;
    } finally {
      if (fileProcessingInterval) clearInterval(fileProcessingInterval);
      fileProcessingInterval = null;
      fileProcessingProgress = 100;
      isProcessingFile = false;
      setTimeout(() => { isFlashing = false; }, 800);
    }
  }

  async function simplifyText() {
    error = null;
    if (!inputText.trim()) { error = "Voer tekst in om te vereenvoudigen"; toast.error(error); return; }
    if (!selectedModel)   { error = "Selecteer eerst een taalmodel"; toast.error(error); return; }
    if (inputWordCount > MAX_WORDS) { error = `De invoertekst (${inputWordCount} woorden) overschrijdt de limiet van ${MAX_WORDS} woorden.`; toast.error(error); return; }
    isLoading = true; outputText = ''; chunkResults = []; totalChunks = 0; receivedChunks = 0; showOutput = true;
    try {
      const response = await fetch(`${WEBUI_BASE_URL}/api/b1/translate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          text: inputText,
          model: selectedModel,
          preserved_words: preservedWords,
          language_level: languageLevel
        })
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
        let message = '';
        if (Array.isArray(errorData.detail)) {
          message = errorData.detail.map(e =>
            (typeof e === 'object' && e !== null && e.msg)
              ? e.msg
              : JSON.stringify(e)
          ).join('; ');
        } else if (typeof errorData.detail === 'object') {
          message = JSON.stringify(errorData.detail);
        } else {
          message = errorData.detail || `HTTP error! status: ${response.status}`;
        }
        toast.error("Fout bij vereenvoudigen: " + message);
        throw new Error(message);
      }
      if (!response.body) throw new Error("Response body is missing");
      const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
      let buffer = '';
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += value;
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const parsed = JSON.parse(line);
            if (parsed.total_chunks !== undefined) {
              totalChunks = parsed.total_chunks; chunkResults = totalChunks > 0 ? Array(totalChunks).fill('') : [];
            } else if (parsed.index !== undefined && parsed.text !== undefined) {
              if (parsed.index >= 0 && parsed.index < totalChunks) {
                chunkResults[parsed.index] = parsed.text;
                receivedChunks++;
                outputText = chunkResults.map(chunk => chunk || '').join('\n');
              }
            }
          } catch (e) {
            console.error('Streamed JSON parse error:', e, line);
          }
        }
      }
      outputText = chunkResults.map(chunk => chunk || '').join('\n');
    } catch (err) {
      error = `Fout: ${err.message}`;
      showOutput = false;
    } finally {
      isLoading = false;
    }
  }

  function addPreservedWord() {
    const word = newPreservedWord.trim();
    if (word && !userWords.includes(word)) userWords = [...userWords, word];
    newPreservedWord = '';
  }
  function removePreservedWord(w) {
    userWords = userWords.filter(word => word !== w);
    activeDefaultWords = activeDefaultWords.filter(word => word !== w);
  }
  $: if (useDefaultWords) activeDefaultWords = [...originalDefaultWords];
  function processText(text) {
    return text ? text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') : '';
  }
</script>

<div class="root-vfill">
  <div class="maxwidthbox">
    <h1 class="title">{languageLevel}-Taalniveau Vereenvoudiger</h1>
    <div class="row settingsrow">
      <div>
        <label class="label">Kies taalmodel:</label>
        {#if availableModels.length > 0}
          <select bind:value={selectedModel}><option value="">Kies...</option>
            {#each availableModels as m}<option value={m.id}>{m.title || m.id}</option>{/each}
          </select>
        {:else}
          <span class="error-text">Geen modellen beschikbaar</span>
        {/if}
      </div>
      <div>
        <label class="label" for="language-level-select">Taalniveau:</label>
        <select id="language-level-select" bind:value={languageLevel}>
          <option value="B1">B1</option><option value="B2">B2</option>
        </select>
      </div>
    </div>
    {#if error}
      <div class="alert-error">{error}</div>
    {/if}
    <div class="presblock">
      <div class="pres-controls">
        <input type="text" bind:value={newPreservedWord} placeholder="Woord toevoegen"
          on:keydown={(e) => e.key === 'Enter' && addPreservedWord()} />
        <button type="button" class="presaddbtn" on:click={addPreservedWord}>Toevoegen</button>
        <label class="checkbox">
          <input type="checkbox" bind:checked={useDefaultWords} /> Standaardtermen ({originalDefaultWords.length})
        </label>
      </div>
      <div class="preserved-tags-scroll">
        {#each preservedWords as word (word)}
          <span class="tag">{word}
            <button class="tag-x" on:click={() => removePreservedWord(word)}>×</button>
          </span>
        {/each}
      </div>
    </div>

    <div class="mainflexfill">
      <!-- Input -->
      <div class="contentbox tallbox">
        <label class="input-label">Originele tekst</label>
        <div class="vfill textarea-holder {isFlashing ? 'flash' : ''} {dragActive ? 'drop-highlight' : ''}"
          on:dragover={handleDrag} on:dragenter={handleDrag}
          on:dragleave={handleDrag} on:drop={handleDrop}>
          <textarea bind:value={inputText} rows="8" disabled={isLoading}
            placeholder="Voer tekst in..." class="textboxarea vfill"></textarea>
        </div>
        <div class="footerrow vfooter">
          <button type="button" class="fileuploadbtn" on:click={()=>fileInput.click()} disabled={isProcessingFile}>
              <svg width="18" height="18" fill="currentColor" viewBox="0 0 20 20"><path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3 3m0 0l-3-3m3 3V8"/></svg>
              Bestand
          </button>
          <input type="file" accept=".doc,.docx,.pdf,.txt,.rtf" class="uploadinvis" bind:this={fileInput} on:change={handleFileInputChange}/>
          <span class="draghint">of sleep bestand hierheen (Word, PDF, TXT, RTF)</span>
          <div class="progressbar-container">
            <div class="progressbar-bar"
              style="width: {(isProcessingFile||fileProcessingProgress===100)?fileProcessingProgress:0}%"></div>
          </div>
          {#if isProcessingFile}
            <div class="progressbarlabel">Bestand verwerken...</div>
          {:else if fileProcessingProgress === 100 && fileProgressDone}
            <div class="progressbarlabel">Bestand verwerkt</div>
          {/if}
          <div class="input-info">
            Aantal woorden: {inputWordCount} / {MAX_WORDS}
          </div>
        </div>
      </div>

      <!-- Pijlknop -->
      <div class="translatecol">
        <button class="vl-btn" type="button" on:click={simplifyText}
          disabled={!inputText || !selectedModel || isLoading}>
          {#if isLoading}
            <span class="spinner"></span>
          {:else}
            <svg width="32" height="32" fill="none" viewBox="0 0 32 32"><circle cx="16" cy="16" r="16" fill="#2563eb"/><path d="M20 12l4 4m0 0l-4 4m4-4H8" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          {/if}
        </button>
      </div>
      <!-- Output -->
      <div class="contentbox tallbox">
        <label class="input-label">Vereenvoudigde tekst</label>
        <div class="vfill outputshow">
          {#if isLoading}
            <span class="busy">Vereenvoudigen, even geduld...</span>
          {/if}
          {#if showOutput}
            <div>{@html processText(outputText)}</div>
            <button class="copybtn" on:click={() => navigator.clipboard.writeText(outputText).then(() => toast.success('Tekst gekopieerd!'))}>Kopieer</button>
          {:else if !isLoading}
            <span class="output-placeholder">Hier verschijnt de vereenvoudigde tekst na verwerking.</span>
          {/if}
        </div>
        <div class="footerrow vfooter">
          <div class="progressbar-container">
            <div class="progressbar-bar" style="width: {(isLoading || outputProgressFinal) ? 100 : 0}%"></div>
          </div>
          <div class="progressbarlabel">
            {#if isLoading}
              {receivedChunks}/{totalChunks} paragrafen verwerkt
            {:else if outputProgressFinal}
              Klaar
            {/if}
          </div>
          <div class="output-info">
            Aantal woorden: {outputWordCount}
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  html, body, #app, .root-vfill { height: 100%; min-height: 100vh; margin: 0; }
  .root-vfill { min-height: 100vh; height: 100vh; background: #f6f8fa; }
  .maxwidthbox { max-width: 1200px; margin: 0 auto; background: #fff; border-radius: 18px; box-shadow:0 4px 24px #0002; padding:2.8rem 2rem; height: 100%; display: flex; flex-direction: column; }
  .title { font-size: 2.1rem; font-weight: 700; color: #20326a; margin-bottom: 1.6rem;}
  .row { display: flex; justify-content: space-between; gap:1.5em; }
  .label {font-size:1rem; font-weight:500;}
  .settingsrow { margin-bottom: 0.6rem;}
  select, input[type="text"] { font-size: 1.01rem; border: 1px solid #b1b7ce; border-radius: 7px; padding:0.45em 0.7em;}
  .alert-error { color: #c0392b; background: #fde8e9; border: 1px solid #e17055;
    border-radius: 7px; padding: 1em 1.2em; font-size: 1rem; margin: 0.7em 0;}
  .presblock {margin-bottom:1.2rem;}
  .pres-controls {display:flex; flex-wrap:wrap; gap:0.5em; align-items:center; margin-bottom:0.3em;}
  .pres-controls input[type="text"] {width:14em;}
  .presaddbtn {border-radius:5px; background:#dbeafe; color:#0c3964; border:none; padding:0.35em 0.95em;}
  .presaddbtn:hover { background: #bbcefa;}
  .checkbox { margin-left: 0.7em; font-size:.98em;}
  .preserved-tags-scroll {max-height: 62px; min-height:34px; overflow-x: hidden; overflow-y:auto; padding:0.4em 0.2em; display:flex; flex-wrap:wrap; gap:0.3em;}
  .tag { background:#e0f2fe; color:#0c3964; border-radius:4px; padding:0.17em 0.6em 0.17em 0.4em; font-size:0.98em; margin-bottom:2px; display:inline-flex; align-items:center;}
  .tag-x { margin-left:0.23em;background:none;border:none;color:#2563eb;font-size:1.13em;font-weight:bold;cursor:pointer;}
  .tag-x:hover{color:#c0392b;}
  .mainflexfill { flex: 1 1 0; display: flex; flex-direction: row; gap: 2.5em; min-height:0; }
  .contentbox.tallbox { flex:1 1 0; display: flex; flex-direction:column; min-width:0; background:#f9fbfe; border-radius: 12px; border: 1.5px solid #dbeafe; padding: 1.2em 1em; position:relative; min-height:0; }
  .input-label {display:block;margin-bottom:.4em;font-size:1em; font-weight:600; color:#26336a;}
  .vfill { flex: 1 1 0; min-height:0;}
  .textarea-holder, .outputshow { display: flex; flex-direction: column; min-height: 0; height: 100%; max-height: 100%; }
  .textboxarea { width: 100%; flex: 1 1 0; min-height:0; max-height:100%; border: none; background: transparent; color: #223; font-size: 1.03em; font-family: inherit; resize: none; }
  .outputshow { white-space: pre-wrap; background: transparent; overflow-y: auto; }
  .input-info, .output-info { font-size:0.91em;color:#7b98b2;margin-top:0.16em;}
  .output-placeholder { color: #a5a8be; }
  .fileuploadbtn { background:#ceedfd; color:#1d3560; border:none; border-radius:5px;padding:0.38em 0.9em; font-size:1em; margin-bottom:0.31em; display:flex;align-items:center;gap:0.5em;cursor:pointer;margin-top:0;}
  .fileuploadbtn svg {vertical-align: middle;}
  .fileuploadbtn:disabled {filter: grayscale(50%);}
  .uploadinvis {display:none;}
  .draghint { color:#788ba7; font-size:.92em; display:block; margin-bottom:0.19em;}
  .drop-highlight { box-shadow:0 0 12px #4ec8f7c0 inset; border-color:#34bbe6;}
  .footerrow.vfooter {
    margin-top: 0;
    margin-bottom: 0;
    min-height: 87px;
    display: flex; flex-direction: column; gap: 0.16em; justify-content: flex-end;
    background: transparent;
    width:100%;
  }
  .progressbar-container { width:100%; height:14px; background:#e8e8fc; border-radius:8px;overflow:hidden;}
  .progressbar-bar {height:14px;background:#2563eb;border-radius:8px;transition:width .17s;}
  .progressbarlabel { font-size:.96em; color: #344388; min-height: 1.4em;}
  .flash { animation:flashkey .95s;}
  @keyframes flashkey {0%{box-shadow:0 0 0 #98b8f6}39%{box-shadow:0 0 32px #8fd6fe;}70%{box-shadow:0 0 0 #9fd8fd;}100%{box-shadow:0 0 0 #9fd8fd;}}
  .translatecol { display: flex; flex-direction: column; align-items: center; justify-content: center;
    min-width:66px;max-width:72px; padding: 0 6px;}
  .vl-btn {
    background:#fff;box-shadow:0 6px 18px #3b82f652; border-radius:50%; border:none; width:58px; height:58px; display:flex; align-items:center; justify-content:center; cursor:pointer; transition: box-shadow 0.19s;
  }
  .vl-btn:hover { box-shadow:0 6px 30px #2563eb33;}
  .vl-btn:disabled { opacity:.65; filter: grayscale(80%);}
  .busy { color:#2563eb; font-style:italic;}
  .spinner {
    border: 4px solid #e3f2fd;
    border-top: 4px solid #2563eb;
    border-radius: 50%;
    width: 32px;
    height: 32px;
    animation: spin .8s linear infinite;
    margin: 0 auto;
  }
  @keyframes spin {
    0% {transform:rotate(0deg);}
    100% {transform:rotate(360deg);}
  }
  .copybtn {
    font-size:0.94em;background:#e5eafd; color:#1d3560; padding:0.36em 0.65em; border:none; border-radius: 5px; margin-top:0.6em; cursor:pointer;
    transition:background .15s;
  }
  .copybtn:hover {background:#bfd4fa;}
  :global(.outputshow strong) {
    font-weight:700;color:#18377f;
  }
  @media(max-width:1080px){.maxwidthbox{max-width:98vw;padding:1.5em 0.5em;}.mainflexfill{gap:1.1em;}}
  @media(max-width:820px){.mainflexfill{flex-direction:column;gap:1.6em;}.translatecol{flex-direction:row;margin-bottom:1em;}}
  @media(max-width:600px){
    .maxwidthbox{padding:1em 0.2em;}
    .settingsrow{flex-direction:column;gap:0.2em;}
    .pres-controls{flex-direction:column;gap:0.2em;}
    .mainflexfill{flex-direction:column;}
    .contentbox.tallbox {height: 420px; min-height: 300px; max-height:600px;}
  }
</style>