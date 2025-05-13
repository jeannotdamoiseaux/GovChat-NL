<script lang="ts">
    import { onMount } from 'svelte';
    import { getContext } from 'svelte';
    import { browser } from '$app/environment'; // Import browser
    import ShortcutsModal from '../chat/ShortcutsModal.svelte';
    import Tooltip from '../common/Tooltip.svelte';
    import Info from '$lib/components/icons/Info.svelte';
    import Modal from '$lib/components/common/Modal.svelte';
    import { sections } from './Help/HelpContent';
    import { WEBUI_NAME } from '$lib/stores';

    let showShortcuts = false;
    let showHelp = false; // Deze wordt gebonden aan de Modal
    let dontShowOnStartup = false;
    const DONT_SHOW_HELP_ON_STARTUP_KEY = 'govchat_dont_show_help_on_startup';

    let isFullScreen = false;
    const i18n = getContext('i18n');

    let activeSection = sections[0].id;
    let openSectionId: string | null = sections[0].id;
    let activeSubsectionId: string | null = null;
    let contentDiv: HTMLDivElement;

    onMount(() => {
        if (browser) {
            const storedPreference = localStorage.getItem(DONT_SHOW_HELP_ON_STARTUP_KEY);
            if (storedPreference === 'true') {
                dontShowOnStartup = true;
                // showHelp blijft de waarde die het had (waarschijnlijk false), dus modal wordt niet getoond
            } else {
                // storedPreference is 'false', null (eerste keer), of iets anders
                dontShowOnStartup = false;
                showHelp = true; // Toon de help modal initieel
            }
        }
    });

    function handleCheckboxChange() {
        if (browser) {
            localStorage.setItem(DONT_SHOW_HELP_ON_STARTUP_KEY, dontShowOnStartup.toString());
        }
    }

    $: if (contentDiv && activeSection) {
        contentDiv.scrollTop = 0;
    }
    function handleSectionLinkClick(id: string, hasSubitems: boolean, event) {
        event.preventDefault();
        openSectionId = id;
        activeSection = id;
        activeSubsectionId = null;
        scrollToSection(id);
    }
    function handleItemClick(parentId: string, itemId: string, event) {
        event.preventDefault();
        openSectionId = parentId;
        activeSection = parentId;
        activeSubsectionId = itemId;
        scrollToSection(itemId);
    }
    function handleSectionDropdownClick(id: string, event) {
        event.stopPropagation();
        openSectionId = openSectionId === id ? null : id;
    }
    function scrollToSection(id: string) {
        const section = document.getElementById(id);
        if (section && contentDiv) {
            const containerTop = contentDiv.getBoundingClientRect().top;
            const sectionTop = section.getBoundingClientRect().top;
            contentDiv.scrollBy({
                top: sectionTop - containerTop,
                behavior: 'smooth'
            });
        }
    }
    function getFullManualHtml() {
        let html = "";
        for (const sec of sections) {
            html += `<section id="${sec.id}" class="mb-8 scroll-mt-24">`;
            html += sec.content;
            html += `</section>`;
            if (sec.items) {
                for (const item of sec.items) {
                    html += `<section id="${item.id}" class="mb-8 scroll-mt-24">`;
                    html += `<div class="font-semibold text-base mb-2">${item.emoji} ${item.title}</div>`;
                    html += item.content;
                    html += `</section>`;
                }
            }
        }
        return html;
    }
    function printHelpContent() {
        // Genereer de handleiding
        const manualHtml = getFullManualHtml();
        const replacedHtml = manualHtml.replace(/{{APP_NAME}}/g, $WEBUI_NAME);
        const printWindow = window.open();
        if (!printWindow) return;
        printWindow.document.write(`<html><head><title>${$i18n.t('Handleiding')} ${$WEBUI_NAME}</title><style>body{font-family: sans-serif;} h2{margin-top: 2em; border-bottom: 1px solid #ccc;} h3{margin-top: 1.5em;}</style></head><body><h1>${$i18n.t('Handleiding')} ${$WEBUI_NAME}</h1>${replacedHtml}</body></html>`);
        printWindow.document.close();
        printWindow.print();
    }
</script>

<!-- Floating helpbutton -->
<div class="hidden lg:flex fixed bottom-0 right-0 px-4.5 py-4.5 z-20">
    <Tooltip content={$i18n.t('Help')} placement="left">
        <button
            id="show-help-button"
            aria-label="Help"
            class="bg-black text-white hover:bg-gray-900
                    dark:bg-white dark:text-black dark:hover:bg-gray-100
                    transition rounded-full py-2.5 px-2.5 self-center
                    flex items-center justify-center
                    size-10 text-3rem font-bold"
            on:click={() => { showHelp = true; }}>
            ?
        </button>
    </Tooltip>
</div>

<Modal bind:show={showHelp} size={isFullScreen ? 'full' : 'lg'} class={isFullScreen ? 'fixed inset-0 z-50' : ''}>
    <div 
     class="px-0 pt-4 dark:text-gray-300 text-gray-700 flex flex-col"
     class:h-[80vh]={!isFullScreen}
     class:h-screen={isFullScreen}
    >
        <!-- Header -->
        <div class="flex justify-between items-start px-5">
            <div class="text-xl font-semibold flex items-center gap-2">
                <Info class="w-6 h-6 text-blue-500" />
                Hulp en uitleg
            </div>
            <div class="flex items-center gap-2">
                <!-- PRINT-KNOP -->
                <button
                class="self-center"
                aria-label="Print handleiding"
                title="Print volledige handleiding"
                on:click={printHelpContent}>
                    <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M6 9V2h12v7M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2m-8 0h8M6 18v2h12v-2"/>
                    </svg>
                </button>
                <!-- FULLSCREEN-KNOP -->
                <button class="self-center" aria-label="Fullscreen"
                on:click={() => isFullScreen = !isFullScreen}
                    title={isFullScreen ? "Verlaat volledig scherm" : "Volledig scherm"}>
                    {#if isFullScreen}
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 20" stroke-width="2" stroke="currentColor" class="w-5 h-5">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M7 3.75H3.75V7M13 3.75h3.25V7M7 16.25H3.75V13M13 16.25h3.25V13"/>
                        </svg>
                    {:else}
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 20" stroke-width="2" stroke="currentColor" class="w-5 h-5">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 7V3.75h3.25M16.25 7V3.75h-3.25M3.75 13V16.25h3.25M16.25 13V16.25h-3.25"/>
                        </svg>
                    {/if}
                </button>
            
                <!-- SLUIT-KNOP -->    
                <button class="self-center" aria-label="Sluiten" title="Sluiten" on:click={() => showHelp = false}>
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-5 h-5">
                    <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                    </svg>
                </button>
            </div>
        </div>
        <div class="mt-1 text-sm text-gray-500 px-5">
            Je kunt je vragen ook direct aan LAICA stellen: de chatbot kent de volledige handleiding!
        </div>
        <div class="flex flex-1 h-0 pt-4 overflow-hidden">
            <!-- Sidebar navigation -->
            <nav aria-label="Help navigatie" class="hidden md:block md:w-64 h-full pr-4 pl-6 flex-shrink-0">
                <ul class="space-y-1">
                    {#each sections as sec}
                        <li class="select-none">
                            <a
                                href={`#${sec.id}`}
                                tabindex="0"
                                class="flex items-center gap-2 px-2 py-1.5 rounded transition-colors cursor-pointer font-medium
                                    {activeSection === sec.id ? 'bg-blue-100 text-blue-700 font-semibold' : 'text-gray-700 dark:text-gray-200 hover:bg-blue-50'}"
                                on:click={(e) => handleSectionLinkClick(sec.id, !!sec.items, e)}
                                aria-expanded={!!sec.items && openSectionId === sec.id}
                                aria-current={activeSection === sec.id ? 'page' : undefined}
                            >
                                <span>{sec.emoji}</span>
                                <span>{sec.title.replace(/{{APP_NAME}}/g, $WEBUI_NAME)}</span>
                                {#if sec.items}
                                    <span
                                        class="ml-auto flex items-center"
                                        title={openSectionId === sec.id ? 'Inklappen' : 'Uitklappen'}
                                        on:click|stopPropagation={(e) => handleSectionDropdownClick(sec.id, e)}
                                        aria-label="Uitklappen"
                                        aria-expanded={openSectionId === sec.id}
                                        tabindex="-1"
                                    >
                                        <svg
                                            class="w-4 h-4 text-gray-400 transition-transform"
                                            style="transform: rotate({openSectionId === sec.id ? 90 : 0}deg)"
                                            viewBox="0 0 20 20" fill="none"
                                        >
                                            <path d="M7 7l3 3 3-3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                        </svg>
                                    </span>
                                {/if}
                            </a>
                            {#if sec.items && openSectionId === sec.id}
                                <ul class="ml-6 border-l border-blue-200 pl-3 mt-1 space-y-1">
                                    {#each sec.items as item}
                                        <li>
                                            <a
                                                href={`#${item.id}`}
                                                tabindex="0"
                                                class="flex items-center gap-2 px-2 py-1.5 rounded transition-colors cursor-pointer text-sm
                                                    {activeSubsectionId === item.id
                                                    ? 'bg-blue-200 text-blue-700 font-semibold'
                                                    : 'text-gray-700 dark:text-gray-200 hover:bg-blue-100'}"
                                                on:click={(e) => handleItemClick(sec.id, item.id, e)}
                                                aria-current={activeSubsectionId === item.id ? 'page' : undefined}
                                            >
                                                <span>{item.emoji}</span>
                                                <span>{item.title.replace(/{{APP_NAME}}/g, $WEBUI_NAME)}</span>
                                            </a>
                                        </li>
                                    {/each}
                                </ul>
                            {/if}
                        </li>
                    {/each}
                </ul>
            </nav>
        
            <!-- Rechter kolom: hoofd-content --> 
            <div class="flex flex-col flex-1 min-w-0">
                <div bind:this={contentDiv} class="flex-1 overflow-y-scroll px-2 md:px-0 pr-2">
                    {#each sections as sec}
                    {#if activeSection === sec.id}
                        <!-- Toon altijd hoofdstuktitel (h2) bovenaan -->
                        <section id={sec.id} class="mb-8 scroll-mt-24">
                        {@html sec.content.replace(/{{APP_NAME}}/g, $WEBUI_NAME)}
                        </section>
                        {#if sec.items}
                        {#each sec.items as item (item.id)}
                            <section id={item.id} class="mb-8 scroll-mt-24">
                            <h3 class="help-section-title">{item.emoji} {item.title.replace(/{{APP_NAME}}/g, $WEBUI_NAME)}</h3>
                            {@html item.content.replace(/{{APP_NAME}}/g, $WEBUI_NAME)}
                            </section>
                        {/each}
                        {/if}
                    {/if}
                    {/each}
                </div>
                <!-- Footer met checkbox en sluitenknop -->
                <div class="flex justify-end items-center space-x-6 pt-3 px-5 shrink-0 mt-6 mb-3">
                    <label class="flex items-center space-x-2 cursor-pointer text-sm text-gray-700 dark:text-gray-300">
                        <input
                            type="checkbox"
                            bind:checked={dontShowOnStartup}
                            on:change={handleCheckboxChange}
                            class="form-checkbox rounded h-4 w-4 text-blue-600 dark:bg-gray-700 dark:border-gray-600 focus:ring-blue-500 transition duration-150 ease-in-out"
                        />
                        <span>{$i18n.t('Niet meer tonen')}</span>
                    </label>
                    <button
                        on:click={() => showHelp = false}
                        class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full"
                    >
                        {$i18n.t('Oke')}
                    </button>
                </div>
            </div>
        </div>
</Modal>
<ShortcutsModal bind:show={showShortcuts} />