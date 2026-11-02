<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import ModelSettingsSection from './ModelSettingsSection.svelte';
	import ModelSettingToggle from './ModelSettingToggle.svelte';
	import BuiltinTools from './BuiltinTools.svelte';
	import { apps } from '$lib/appList'; // GovChat-NL: app-gebonden capabilities

	// GovChat-NL: apps met een eigen toegangsrecht (zoals voorheen: Chat en Versimpelaar)
	const appAccessApps = apps.filter((app) => app.capabilityKey);

	const i18n: Writable<i18nType> = getContext('i18n');

	let capabilityLabels;
	$: capabilityLabels = {
		vision: {
			label: $i18n.t('settings.admin.models.capabilities.vision.label'),
			description: $i18n.t('settings.admin.models.capabilities.vision.description')
		},
		file_upload: {
			label: $i18n.t('settings.admin.models.capabilities.fileUpload.label'),
			description: $i18n.t('settings.admin.models.capabilities.fileUpload.description')
		},
		file_context: {
			label: $i18n.t('settings.admin.models.capabilities.fileContext.label'),
			description: $i18n.t('settings.admin.models.capabilities.fileContext.description')
		},
		web_search: {
			label: $i18n.t('settings.admin.models.capabilities.webSearch.label'),
			description: $i18n.t('settings.admin.models.capabilities.webSearch.description')
		},
		image_generation: {
			label: $i18n.t('settings.admin.models.capabilities.imageGeneration.label'),
			description: $i18n.t('settings.admin.models.capabilities.imageGeneration.description')
		},
		code_interpreter: {
			label: $i18n.t('settings.admin.models.capabilities.codeInterpreter.label'),
			description: $i18n.t('settings.admin.models.capabilities.codeInterpreter.description')
		},
		terminal: {
			label: $i18n.t('settings.admin.models.capabilities.terminal.label'),
			description: $i18n.t('settings.admin.models.capabilities.terminal.description')
		},
		usage: {
			label: $i18n.t('settings.admin.models.capabilities.usage.label'),
			description: $i18n.t('settings.admin.models.capabilities.usage.description')
		},
		citations: {
			label: $i18n.t('settings.admin.models.capabilities.citations.label'),
			description: $i18n.t('settings.admin.models.capabilities.citations.description')
		},
		status_updates: {
			label: $i18n.t('settings.admin.models.capabilities.statusUpdates.label'),
			description: $i18n.t('settings.admin.models.capabilities.statusUpdates.description')
		},
		memory: {
			label: $i18n.t('settings.admin.models.capabilities.memory.label'),
			description: $i18n.t('settings.admin.models.capabilities.memory.description')
		},
		builtin_tools: {
			label: $i18n.t('settings.admin.models.capabilities.builtinTools.label'),
			description: $i18n.t('settings.admin.models.capabilities.builtinTools.description')
		}
	};

	type Capability = keyof typeof capabilityLabels;

	export let capabilities: Partial<Record<Capability, boolean>> = {};

	export let defaultFeatureIds: string[] = [];
	export let builtinTools: Record<string, boolean> = {};
	export let disabled = false;
	const featureKeys: Capability[] = ['web_search', 'image_generation', 'code_interpreter'];
	$: visibleCapabilities = (Object.keys(capabilityLabels) as Capability[]).filter(
		(key) => key !== 'file_context' || capabilities.file_upload
	);
	$: enabledCapabilityIds = visibleCapabilities.filter((key) => capabilities[key]);
	$: availableFeatures = featureKeys.filter((key) => capabilities[key]);
	$: enabledDefaultIds = availableFeatures.filter((key) => defaultFeatureIds.includes(key));
	const setDefault = (key: string, enabled: boolean) => {
		defaultFeatureIds = enabled
			? [...new Set([...defaultFeatureIds, key])]
			: defaultFeatureIds.filter((id) => id !== key);
	};
</script>

<div class="space-y-0.5">
	<ModelSettingsSection
		label={$i18n.t('settings.admin.models.capabilities.title')}
		description={$i18n.t(
			'Choose which features are available for this model. The connected model and provider must support them.'
		)}
	>
		<span slot="summary" class="flex min-w-0 items-center gap-1 text-gray-900 dark:text-gray-100">
			<span class="min-w-0 truncate"
				>{enabledCapabilityIds
					.slice(0, 3)
					.map((key) => capabilityLabels[key].label)
					.join(', ') || $i18n.t('None')}</span
			>
			{#if enabledCapabilityIds.length > 3}<span class="shrink-0 text-gray-500"
					>+{enabledCapabilityIds.length - 3}</span
				>{/if}
		</span>
		<div class="grid grid-cols-1 gap-x-6 sm:grid-cols-2 lg:grid-cols-3">
			{#each visibleCapabilities as key}
				<ModelSettingToggle
					label={capabilityLabels[key].label}
					description={capabilityLabels[key].description}
					bind:checked={capabilities[key]}
					{disabled}
				/>
			{/each}
		</div>
	</ModelSettingsSection>

	<!-- Previous DefaultFeatures labels retained for i18n extraction:
	{$i18n.t('settings.admin.models.defaultFeatures.webSearch.label')}
	{$i18n.t('settings.admin.models.defaultFeatures.webSearch.description')}
	{$i18n.t('settings.admin.models.defaultFeatures.imageGeneration.label')}
	{$i18n.t('settings.admin.models.defaultFeatures.imageGeneration.description')}
	{$i18n.t('settings.admin.models.defaultFeatures.codeInterpreter.label')}
	{$i18n.t('settings.admin.models.defaultFeatures.codeInterpreter.description')}
	-->
	{#if availableFeatures.length}
		<ModelSettingsSection
			label={$i18n.t('settings.admin.models.defaultFeatures.title')}
			description={$i18n.t('Choose which available features start enabled in new chats.')}
		>
			<span slot="summary" class="flex min-w-0 items-center gap-1 text-gray-900 dark:text-gray-100">
				<span class="min-w-0 truncate"
					>{enabledDefaultIds
						.slice(0, 3)
						.map((key) => capabilityLabels[key].label)
						.join(', ') || $i18n.t('None')}</span
				>
				{#if enabledDefaultIds.length > 3}<span class="shrink-0 text-gray-500"
						>+{enabledDefaultIds.length - 3}</span
					>{/if}
			</span>
			<p class="mb-1 px-1 text-xs text-gray-500 dark:text-gray-400">
				{$i18n.t('Start enabled in new chats')}
			</p>
			<div class="grid grid-cols-1 gap-x-6 sm:grid-cols-2 lg:grid-cols-3">
				{#each availableFeatures as key}
					<ModelSettingToggle
						label={capabilityLabels[key].label}
						checked={defaultFeatureIds.includes(key)}
						{disabled}
						on:change={(e) => setDefault(key, e.detail)}
					/>
				{/each}
			</div>
		</ModelSettingsSection>
	{/if}

	<!-- GovChat-NL: toegang tot apps -->
	{#if appAccessApps.length > 0}
		<ModelSettingsSection
			label="App Toegang"
			description="Kies in welke GovChat-NL-apps dit model beschikbaar is."
		>
			<span slot="summary" class="min-w-0 truncate text-gray-900 dark:text-gray-100"
				>{appAccessApps
					.filter((app) => capabilities[app.capabilityKey])
					.map((app) => app.name)
					.join(', ') || $i18n.t('None')}</span
			>
			<div class="grid grid-cols-1 gap-x-6 sm:grid-cols-2 lg:grid-cols-3">
				{#each appAccessApps as app}
					<ModelSettingToggle
						label={app.name}
						description={`Model is beschikbaar voor de ${app.name} app`}
						bind:checked={capabilities[app.capabilityKey]}
						{disabled}
					/>
				{/each}
			</div>
		</ModelSettingsSection>
	{/if}

	<!-- GovChat-NL: App Launcher-app -->
	<ModelSettingsSection
		label="App Launcher"
		description="Toon dit model als eigen app-tegel in de App Launcher. Combineer met een systeemprompt en gekoppelde kennis (bijv. PDF-documenten) om een taakgerichte app te maken, zoals een CAO-vragenbeantwoorder."
	>
		<span slot="summary" class="min-w-0 truncate text-gray-900 dark:text-gray-100"
			>{capabilities.app_launcher_entry ? 'Toon als app' : $i18n.t('None')}</span
		>
		<ModelSettingToggle
			label="Toon als app in de App Launcher"
			bind:checked={capabilities.app_launcher_entry}
			{disabled}
		/>
	</ModelSettingsSection>

	{#if capabilities.builtin_tools}
		<BuiltinTools bind:builtinTools {disabled} />
	{/if}
</div>
