<script lang="ts">
	import { models, showSettings, settings, user, mobile, config } from '$lib/stores';
	// Govchat
	import { filteredModels, currentAppContext } from '$lib/stores/appModels';
	import { onMount, tick, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import Selector from './ModelSelector/Selector.svelte';
	import Tooltip from '../common/Tooltip.svelte';

	import { updateUserSettings } from '$lib/apis/users';
	const i18n = getContext('i18n');

	export let selectedModels = [''];
	export let disabled = false;
	export let showSetDefault = true;
	// Govchat
	export let useAppFilter = false; // New prop to enable app-specific filtering

	// Prevent multiple rapid auto-selections
	let autoSelectionInProgress = false;

	// Use either filtered models or all models based on useAppFilter prop
	$: availableModels = useAppFilter ? $filteredModels : $models;

	// Show warning if app filter is enabled but no models are available
	// Only show warning after initial load to prevent showing on page load
	let initialLoadDone = false;
	$: if (useAppFilter && $models && $models.length > 0) {
		if ($filteredModels.length === 0) {
			if (initialLoadDone) {
				const appType = $currentAppContext === 'b1' ? 'B1 Taalniveau' : 'Subsidie';
				toast.warning(`Geen modellen beschikbaar voor ${appType} app. Neem contact op met de administrator.`);
			}
		} else {
			initialLoadDone = true;
		}
	}

	// Auto-select first available model when app context changes or when models become available
	$: if (useAppFilter && $filteredModels && $filteredModels.length > 0 && !autoSelectionInProgress) {
		// If using app filter and current selection is not available in filtered models
		const currentModel = selectedModels[0];
		const isCurrentModelValid = currentModel && $filteredModels.some(m => m.id === currentModel);
		
		if (!isCurrentModelValid) {
			autoSelectionInProgress = true;
			selectedModels = [$filteredModels[0].id];
			console.log(`[ModelSelector] Auto-selected model for ${$currentAppContext} app:`, $filteredModels[0].name, 'ID:', $filteredModels[0].id);
			// Reset flag after a shorter delay to improve responsiveness
			setTimeout(() => {
				autoSelectionInProgress = false;
			}, 50);
		}
	}

	const saveDefaultModel = async () => {
		const hasEmptyModel = selectedModels.filter((it) => it === '');
		if (hasEmptyModel.length) {
			toast.error($i18n.t('Choose a model before saving...'));
			return;
		}
		settings.set({ ...$settings, models: selectedModels });
		await updateUserSettings(localStorage.token, { ui: $settings });

		toast.success($i18n.t('Default model updated'));
	};

	$: if (selectedModels.length > 0 && availableModels.length > 0) {
		selectedModels = selectedModels.map((model) =>
			availableModels.map((m) => m.id).includes(model) ? model : ''
		);
	}

	// Auto-select first available model if no valid model is selected
	$: if (availableModels && availableModels.length > 0 && !autoSelectionInProgress) {
		// Check if any selected model is empty or invalid
		const hasEmptyOrInvalidModel = selectedModels.some(model => 
			!model || !availableModels.some(m => m.id === model)
		);
		
		// If we have empty/invalid models, replace them with the first available model
		if (hasEmptyOrInvalidModel) {
			autoSelectionInProgress = true;
			selectedModels = selectedModels.map(model => {
				if (!model || !availableModels.some(m => m.id === model)) {
					return availableModels[0].id;
				}
				return model;
			});
			// Reset flag after a brief delay
			setTimeout(() => {
				autoSelectionInProgress = false;
			}, 100);
		}
		
		// If selectedModels is empty or has only empty strings, add first available model
		if (selectedModels.length === 0 || selectedModels.every(model => !model)) {
			autoSelectionInProgress = true;
			selectedModels = [availableModels[0].id];
			setTimeout(() => {
				autoSelectionInProgress = false;
			}, 100);
		}
	}
</script>

<div class="flex flex-col w-full items-start">
	{#each selectedModels as selectedModel, selectedModelIdx}
		<div class="flex w-full max-w-fit">
			<div class="overflow-hidden w-full">
				<div class="mr-1 max-w-full">
					<Selector
						id={`${selectedModelIdx}`}
						placeholder={$i18n.t('Select a model')}
						items={availableModels.map((model) => ({
							value: model.id,
							label: model.name,
							model: model
						}))}
						showTemporaryChatControl={$user?.role === 'user'
							? ($user?.permissions?.chat?.temporary ?? true) &&
								!($user?.permissions?.chat?.temporary_enforced ?? false)
							: true}
						bind:value={selectedModel}
					/>
				</div>
			</div>

			{#if $user?.role === 'admin' || ($user?.permissions?.chat?.multiple_models ?? true)}
				{#if selectedModelIdx === 0}
					<div
						class="  self-center mx-1 disabled:text-gray-600 disabled:hover:text-gray-600 -translate-y-[0.5px]"
					>
						<Tooltip content={$i18n.t('Add Model')}>
							<button
								class=" "
								{disabled}
								on:click={() => {
									selectedModels = [...selectedModels, ''];
								}}
								aria-label="Add Model"
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="2"
									stroke="currentColor"
									class="size-3.5"
								>
									<path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12m6-6H6" />
								</svg>
							</button>
						</Tooltip>
					</div>
				{:else}
					<div
						class="  self-center mx-1 disabled:text-gray-600 disabled:hover:text-gray-600 -translate-y-[0.5px]"
					>
						<Tooltip content={$i18n.t('Remove Model')}>
							<button
								{disabled}
								on:click={() => {
									selectedModels.splice(selectedModelIdx, 1);
									selectedModels = selectedModels;
								}}
								aria-label="Remove Model"
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="2"
									stroke="currentColor"
									class="size-3"
								>
									<path stroke-linecap="round" stroke-linejoin="round" d="M19.5 12h-15" />
								</svg>
							</button>
						</Tooltip>
					</div>
				{/if}
			{/if}
		</div>
	{/each}
</div>

{#if $config?.customization?.enable_multiple_models}
	{#if showSetDefault}
		<div class=" absolute text-left mt-[1px] ml-1 text-[0.7rem] text-gray-500 font-primary">
			<button on:click={saveDefaultModel}> {$i18n.t('Set as default')}</button>
		</div>
	{/if}
{/if}