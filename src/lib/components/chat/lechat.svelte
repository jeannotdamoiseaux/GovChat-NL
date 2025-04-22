<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	const i18n: any = getContext('i18n');

	import { page } from '$app/stores';

	import {
		chatId,
		config,
		settings,
		showSidebar,
		WEBUI_NAME,
		chatTitle,
		models
	} from '$lib/stores';
	import { updateUserSettings } from '$lib/apis/users';

	import Navbar from '$lib/components/chat/Navbar.svelte';
	import B1Logic from '../app-launcher/b1-taalniveau/b1-logic.svelte';

	export let chatIdProp = '';

	let loading = false;
	let selectedModels = [''];

	// Functie om geselecteerde modellen op te slaan in localStorage
	function saveSelectedModels() {
		if (selectedModels.length === 0 || (selectedModels.length === 1 && selectedModels[0] === '')) {
			return;
		}
		localStorage.setItem('lechat_selected_models', JSON.stringify(selectedModels));
		console.log('Saved selected models to localStorage:', selectedModels);
	}

	// Functie om geselecteerde modellen te laden uit localStorage
	function loadSelectedModels() {
		try {
			const savedModels = localStorage.getItem('lechat_selected_models');
			if (savedModels) {
				const parsedModels = JSON.parse(savedModels);
				if (Array.isArray(parsedModels) && parsedModels.length > 0) {
					selectedModels = parsedModels;
					console.log('Loaded selected models from localStorage:', selectedModels);
				}
			}
		} catch (error) {
			console.error("Error loading saved models:", error);
		}
	}

	// Functie om geselecteerde modellen op te slaan in gebruikersinstellingen
	async function saveDefaultModel() {
		const hasEmptyModel = selectedModels.filter(it => it === '');
		if (hasEmptyModel.length) {
			toast.error($i18n.t('Kies een model voordat je het opslaat...'));
			return;
		}
		
		try {
			// Update lokale instellingen
			settings.set({ ...$settings, models: selectedModels });
			
			// Update gebruikersinstellingen op de server
			await updateUserSettings(localStorage.token, { ui: $settings });
			
			toast.success($i18n.t('Standaard model bijgewerkt'));
		} catch (error) {
			console.error("Error saving default model:", error);
			toast.error($i18n.t('Fout bij opslaan van standaard model'));
		}
	}

	// Eenvoudige functie om de pagina te herladen
	const initNewChat = async () => {
		console.log("New chat initialized (simplified)");
		window.location.reload();
	};

	// Reactieve statement om modellen op te slaan wanneer ze veranderen
	$: if (selectedModels) {
		saveSelectedModels();
	}

	onMount(() => {
		console.log("Simplified chat component with model selector mounted");
		
		// Laad opgeslagen modellen
		loadSelectedModels();
		
		// Als er geen opgeslagen modellen zijn en er zijn modellen beschikbaar, selecteer het eerste model
		if ((selectedModels.length === 0 || (selectedModels.length === 1 && selectedModels[0] === '')) && $models && $models.length > 0) {
			selectedModels = [$models[0].id];
		}
		
		// Controleer of de geselecteerde modellen nog bestaan
		if (selectedModels.length > 0 && $models && $models.length > 0) {
			selectedModels = selectedModels.map(modelId => 
				$models.map(m => m.id).includes(modelId) ? modelId : ''
			);
			
			// Als er geen geldig model is, selecteer het eerste beschikbare model
			if (selectedModels.every(m => m === '')) {
				selectedModels = [$models[0].id];
			}
		}
	});
</script>

<svelte:head>
	<title>
		{$chatTitle
			? `${$chatTitle.length > 30 ? `${$chatTitle.slice(0, 30)}...` : $chatTitle} | ${$WEBUI_NAME}`
			: `${$WEBUI_NAME}`}
	</title>
</svelte:head>

<div
	class="h-screen max-h-[100dvh] transition-width duration-200 ease-in-out {$showSidebar
		? '  md:max-w-[calc(100%-260px)]'
		: ' '} w-full max-w-full flex flex-col"
	id="chat-container"
>
	{#if chatIdProp === '' || (!loading && chatIdProp)}
		{#if $settings?.backgroundImageUrl ?? null}
			<div
				class="absolute {$showSidebar
					? 'md:max-w-[calc(100%-260px)] md:translate-x-[260px]'
					: ''} top-0 left-0 w-full h-full bg-cover bg-center bg-no-repeat"
				style="background-image: url({$settings.backgroundImageUrl})  "
			/>

			<div
				class="absolute top-0 left-0 w-full h-full bg-linear-to-t from-white to-white/85 dark:from-gray-900 dark:to-gray-900/90 z-0"
			/>
		{/if}

		<!-- Navbar met model selector -->
		<Navbar
			chat={{
				id: $chatId,
				chat: {
					title: $chatTitle,
					models: selectedModels,
					system: $settings.system ?? undefined,
					params: {},
					history: { messages: {}, currentId: null },
					timestamp: Date.now()
				}
			}}
			title={$chatTitle || "GovChat-NL"}
			bind:selectedModels
			shareEnabled={false}
			{initNewChat}
		/>

		<div class="flex-1 flex flex-col z-10 w-full @container">
			<slot name="content">
				<div class="flex-grow flex items-center justify-center">
					<div class="text-center p-8">
						<h1 class="text-2xl font-bold text-gray-700 dark:text-gray-200 mb-4">
							{$WEBUI_NAME}
						</h1>
						<p class="text-gray-500 dark:text-gray-400 mb-4">
							Deze pagina is momenteel leeg. Gebruik de model selector hierboven om een model te kiezen.
						</p>
						
						{#if selectedModels[0]}
							<div class="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg inline-block">
								<p class="text-blue-700 dark:text-blue-300 mb-2">
									Geselecteerd model: <span class="font-semibold">{$models.find(m => m.id === selectedModels[0])?.name || selectedModels[0]}</span>
								</p>
								
								<button 
									on:click={saveDefaultModel}
									class="mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium transition-colors"
								>
									Stel in als standaard model
								</button>
							</div>
						{/if}
					</div>
				</div>
			</slot>
		</div>
	{:else if loading}
		<div class="flex items-center justify-center h-full w-full">
			<div class="m-auto">
				<div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gray-500"></div>
			</div>
		</div>
	{/if}
</div>