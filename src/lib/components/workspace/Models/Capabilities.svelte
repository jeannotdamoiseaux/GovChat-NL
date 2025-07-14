<script lang="ts">
	import { getContext } from 'svelte';
	import Checkbox from '$lib/components/common/Checkbox.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import { marked } from 'marked';
	import { apps } from '$lib/appList'; // GovChat-NL: Importing app list for capabilities

	const i18n = getContext('i18n');

	// Dynamisch ophalen van de app-gebonden capabilities (behalve Chat)
  	const appAccessApps = apps.filter(app => 
		app.capabilityKey
	);
	export let capabilities: { [key: string]: boolean } = {};

	const staticLabels = { // GovChat-NL: Static labels for existing capabilities 
		vision: {
			label: $i18n.t('Vision'),
			description: $i18n.t('Model accepts image inputs')
		},
		file_upload: {
			label: $i18n.t('File Upload'),
			description: $i18n.t('Model accepts file inputs')
		},
		web_search: {
			label: $i18n.t('Web Search'),
			description: $i18n.t('Model can search the web for information')
		},
		image_generation: {
			label: $i18n.t('Image Generation'),
			description: $i18n.t('Model can generate images based on text prompts')
		},
		code_interpreter: {
			label: $i18n.t('Code Interpreter'),
			description: $i18n.t('Model can execute code and perform calculations')
		},
		usage: {
			label: $i18n.t('Usage'),
			description: $i18n.t(
				'Sends `stream_options: { include_usage: true }` in the request.\nSupported providers will return token usage information in the response when set.'
			)
		},
		citations: {
            label: $i18n.t('Citations'),
            description: $i18n.t('Displays citations in the response')
        }
    };

    const dynamicLabels = Object.fromEntries( // GovChat-NL: Dynamically create labels for app access capabilities
        appAccessApps.map(app => [
            app.capabilityKey,
            {
                label: app.name,
                description: `Model is beschikbaar voor de ${app.name} app`
            }
        ])
    );

    const capabilityLabels = { ...staticLabels, ...dynamicLabels }; // GovChat-NL: Combine static and dynamic labels

</script>

<div>
	<div class="flex w-full justify-between mb-1">
		<div class=" self-center text-sm font-semibold">{$i18n.t('Capabilities')}</div>
	</div>
	<div class="flex items-center mt-2 flex-wrap">
		{#each Object.keys(capabilityLabels).filter(cap => !cap.endsWith('_app_access')) as capability}
			<div class=" flex items-center gap-2 mr-3">
				<Checkbox
					state={capabilities[capability] ? 'checked' : 'unchecked'}
					on:change={(e) => {
						capabilities[capability] = e.detail === 'checked';
					}}
				/>

				<div class=" py-0.5 text-sm capitalize">
					<Tooltip content={marked.parse(capabilityLabels[capability].description)}>
						{$i18n.t(capabilityLabels[capability].label)}
					</Tooltip>
				</div>
			</div>
		{/each}
	</div>

	<!-- App Access Section --> 
	<div class="flex w-full justify-between mb-1 mt-4">
		<div class=" self-center text-sm font-semibold">App Toegang</div>
	</div>
	<div class="flex items-center mt-2 flex-wrap">
		{#each Object.keys(capabilityLabels).filter(cap => cap.endsWith('_app_access')) as capability}
			<div class=" flex items-center gap-2 mr-3">
				<Checkbox
					state={capabilities[capability] ? 'checked' : 'unchecked'}
					on:change={(e) => {
						capabilities[capability] = e.detail === 'checked';
					}}
				/>

				<div class=" py-0.5 text-sm capitalize">
					<Tooltip content={marked.parse(capabilityLabels[capability].description)}>
						{capabilityLabels[capability].label}
					</Tooltip>
				</div>
			</div>
		{/each}
	</div>
</div>