<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { getGovChatNLConfig, setGovChatNLConfig } from '$lib/apis/configs';
	import { defaultSections } from '$lib/components/layout/Help/HelpContent';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	const i18n = getContext('i18n');

	export let saveHandler: Function;

	let loading = true;

	// Versimpelaar config
	let b1PreservedWords: string[] = [];
	let newWord = '';

	// Handleiding config
	let helpHiddenSections: string[] = [];
	let helpCustomSections: object[] = [];

	// New custom section form
	let showAddSection = false;
	let newSection = {
		id: '',
		emoji: '',
		title: '',
		content: '',
		position: 'before' as 'before' | 'after',
		order: 0
	};

	const loadConfig = async () => {
		try {
			const config = await getGovChatNLConfig(localStorage.token);
			if (config) {
				b1PreservedWords = config.b1_default_preserved_words || [];
				helpHiddenSections = config.help_hidden_default_sections || [];
				helpCustomSections = config.help_custom_sections || [];
			}
		} catch (error) {
			toast.error($i18n.t('Failed to load GovChat-NL config'));
			console.error(error);
		}
		loading = false;
	};

	const saveConfig = async () => {
		try {
			await setGovChatNLConfig(localStorage.token, {
				b1_default_preserved_words: b1PreservedWords,
				help_hidden_default_sections: helpHiddenSections,
				help_custom_sections: helpCustomSections
			});
			saveHandler();
		} catch (error) {
			toast.error($i18n.t('Failed to save GovChat-NL config'));
			console.error(error);
		}
	};

	// Versimpelaar functions
	const addWord = () => {
		if (newWord.trim() && !b1PreservedWords.includes(newWord.trim())) {
			b1PreservedWords = [...b1PreservedWords, newWord.trim()];
			newWord = '';
		}
	};

	const removeWord = (word: string) => {
		b1PreservedWords = b1PreservedWords.filter((w) => w !== word);
	};

	// Handleiding functions
	const toggleSectionVisibility = (sectionId: string) => {
		if (helpHiddenSections.includes(sectionId)) {
			helpHiddenSections = helpHiddenSections.filter((id) => id !== sectionId);
		} else {
			helpHiddenSections = [...helpHiddenSections, sectionId];
		}
	};

	const addCustomSection = () => {
		if (newSection.title.trim()) {
			const section = {
				...newSection,
				id: `custom-${Date.now()}`,
				order: helpCustomSections.length
			};
			helpCustomSections = [...helpCustomSections, section];
			newSection = { id: '', emoji: '', title: '', content: '', position: 'before', order: 0 };
			showAddSection = false;
		}
	};

	const removeCustomSection = (id: string) => {
		helpCustomSections = helpCustomSections.filter((s: any) => s.id !== id);
	};

	onMount(async () => {
		await loadConfig();
	});
</script>

{#if loading}
	<div class="flex justify-center py-8">
		<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-white"></div>
	</div>
{:else}
	<form
		class="flex flex-col h-full justify-between space-y-3 text-sm"
		on:submit|preventDefault={saveConfig}
	>
		<div class="overflow-y-scroll scrollbar-hidden h-full pr-1.5">
			<!-- Versimpelaar Section -->
			<div class="mb-6">
				<div class="mt-0.5 mb-2.5 text-base font-medium">{$i18n.t('Versimpelaar - B1 Woorden')}</div>
				<p class="text-xs text-gray-500 dark:text-gray-400 mb-3">
					{$i18n.t('Woorden die behouden blijven bij het versimpelen naar B1-taalniveau.')}
				</p>

				<div class="flex gap-2 mb-3">
					<input
						type="text"
						bind:value={newWord}
						placeholder={$i18n.t('Nieuw woord toevoegen...')}
						class="flex-1 rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none"
						on:keydown={(e) => e.key === 'Enter' && (e.preventDefault(), addWord())}
					/>
					<button
						type="button"
						class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700 transition"
						on:click={addWord}
					>
						{$i18n.t('Toevoegen')}
					</button>
				</div>

				<div class="flex flex-wrap gap-2 p-3 bg-gray-50 dark:bg-gray-850 rounded-lg min-h-[60px]">
					{#each b1PreservedWords as word}
						<span
							class="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-sm"
						>
							{word}
							<button
								type="button"
								class="ml-1 hover:text-red-600 transition"
								on:click={() => removeWord(word)}
							>
								<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
									<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
								</svg>
							</button>
						</span>
					{/each}
					{#if b1PreservedWords.length === 0}
						<span class="text-gray-400 text-sm">{$i18n.t('Geen woorden toegevoegd')}</span>
					{/if}
				</div>
			</div>

			<hr class="border-gray-100 dark:border-gray-850 my-4" />

			<!-- Handleiding Section -->
			<div class="mb-6">
				<div class="mt-0.5 mb-2.5 text-base font-medium">{$i18n.t('Handleiding - Standaard Secties')}</div>
				<p class="text-xs text-gray-500 dark:text-gray-400 mb-3">
					{$i18n.t('Bepaal welke standaard handleiding secties zichtbaar zijn.')}
				</p>

				<div class="space-y-2">
					{#each defaultSections as section}
						<div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-850 rounded-lg">
							<div class="flex items-center gap-2">
								<span>{section.emoji}</span>
								<span class="font-medium">{section.title}</span>
							</div>
							<button
								type="button"
								class="px-3 py-1 rounded text-sm transition {helpHiddenSections.includes(section.id)
									? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
									: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'}"
								on:click={() => toggleSectionVisibility(section.id)}
							>
								{helpHiddenSections.includes(section.id) ? $i18n.t('Verborgen') : $i18n.t('Zichtbaar')}
							</button>
						</div>
					{/each}
				</div>
			</div>

			<hr class="border-gray-100 dark:border-gray-850 my-4" />

			<!-- Custom Sections -->
			<div class="mb-6">
				<div class="flex items-center justify-between mt-0.5 mb-2.5">
					<div class="text-base font-medium">{$i18n.t('Handleiding - Eigen Secties')}</div>
					<button
						type="button"
						class="px-3 py-1 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700 transition"
						on:click={() => (showAddSection = !showAddSection)}
					>
						{showAddSection ? $i18n.t('Annuleren') : $i18n.t('Sectie Toevoegen')}
					</button>
				</div>

				{#if showAddSection}
					<div class="p-4 bg-gray-50 dark:bg-gray-850 rounded-lg mb-4 space-y-3">
						<div class="grid grid-cols-2 gap-3">
							<input
								type="text"
								bind:value={newSection.emoji}
								placeholder={$i18n.t('Emoji (bijv. 🏛️)')}
								class="rounded-lg py-2 px-4 text-sm bg-white dark:bg-gray-800 outline-none"
							/>
							<input
								type="text"
								bind:value={newSection.title}
								placeholder={$i18n.t('Titel')}
								class="rounded-lg py-2 px-4 text-sm bg-white dark:bg-gray-800 outline-none"
							/>
						</div>
						<textarea
							bind:value={newSection.content}
							placeholder={$i18n.t('Inhoud (HTML toegestaan)')}
							rows="4"
							class="w-full rounded-lg py-2 px-4 text-sm bg-white dark:bg-gray-800 outline-none"
						></textarea>
						<div class="flex items-center gap-4">
							<label class="flex items-center gap-2">
								<input type="radio" bind:group={newSection.position} value="before" />
								<span class="text-sm">{$i18n.t('Voor standaard secties')}</span>
							</label>
							<label class="flex items-center gap-2">
								<input type="radio" bind:group={newSection.position} value="after" />
								<span class="text-sm">{$i18n.t('Na standaard secties')}</span>
							</label>
						</div>
						<button
							type="button"
							class="px-4 py-2 rounded-lg bg-green-600 text-white text-sm hover:bg-green-700 transition"
							on:click={addCustomSection}
						>
							{$i18n.t('Sectie Opslaan')}
						</button>
					</div>
				{/if}

				<div class="space-y-2">
					{#each helpCustomSections as section}
						<div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-850 rounded-lg">
							<div class="flex items-center gap-2">
								<span>{section.emoji || '📄'}</span>
								<span class="font-medium">{section.title}</span>
								<span class="text-xs text-gray-400">
									({section.position === 'before' ? $i18n.t('voor') : $i18n.t('na')} standaard)
								</span>
							</div>
							<button
								type="button"
								class="px-3 py-1 rounded bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300 text-sm hover:bg-red-200 transition"
								on:click={() => removeCustomSection(section.id)}
							>
								{$i18n.t('Verwijderen')}
							</button>
						</div>
					{/each}
					{#if helpCustomSections.length === 0}
						<p class="text-gray-400 text-sm p-3">{$i18n.t('Geen eigen secties toegevoegd')}</p>
					{/if}
				</div>
			</div>
		</div>

		<div class="flex justify-end pt-3">
			<button
				type="submit"
				class="px-4 py-2 rounded-lg bg-black text-white dark:bg-white dark:text-black text-sm font-medium hover:bg-gray-900 dark:hover:bg-gray-100 transition"
			>
				{$i18n.t('Opslaan')}
			</button>
		</div>
	</form>
{/if}
