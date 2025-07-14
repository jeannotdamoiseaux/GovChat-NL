<script lang="ts">
	import { getContext } from 'svelte';
	import Checkbox from '$lib/components/common/Checkbox.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import { marked } from 'marked';

	const i18n: any = getContext('i18n');

	// Define capability labels using i18n function with fallback
	$: capabilityLabels = {
		vision: {
			label: i18n?.t?.('Vision') || 'Vision',
			description: i18n?.t?.('Model accepts image inputs') || 'Model accepts image inputs'
		},
		file_upload: {
			label: i18n?.t?.('File Upload') || 'File Upload',
			description: i18n?.t?.('Model accepts file inputs') || 'Model accepts file inputs'
		},
		web_search: {
			label: i18n?.t?.('Web Search') || 'Web Search',
			description: i18n?.t?.('Model can search the web for information') || 'Model can search the web for information'
		},
		image_generation: {
			label: i18n?.t?.('Image Generation') || 'Image Generation',
			description: i18n?.t?.('Model can generate images based on text prompts') || 'Model can generate images based on text prompts'
		},
		code_interpreter: {
			label: i18n?.t?.('Code Interpreter') || 'Code Interpreter',
			description: i18n?.t?.('Model can execute code and perform calculations') || 'Model can execute code and perform calculations'
		},
		usage: {
			label: i18n?.t?.('Usage') || 'Usage',
			description: i18n?.t?.(
				'Sends `stream_options: { include_usage: true }` in the request.\nSupported providers will return token usage information in the response when set.'
			) || 'Sends `stream_options: { include_usage: true }` in the request.\nSupported providers will return token usage information in the response when set.'
		},
		citations: {
			label: i18n?.t?.('Citations') || 'Citations',
			description: i18n?.t?.('Displays citations in the response') || 'Displays citations in the response'
		},
		b1_app_access: {
			label: 'B1 Taalniveau',
			description: 'Model is beschikbaar voor de B1 Taalniveau vereenvoudigings-app'
		},
		subsidie_app_access: {
			label: 'Subsidie App',
			description: 'Model is beschikbaar voor de subsidie beoordeling en analyse app'
		},
		general_chat_app_access: {
			label: 'Algemene Chat',
			description: 'Model is beschikbaar in de algemene chat functionaliteit'
		}
	} as Record<string, { label: string; description: string }>;

	export let capabilities: {
		vision?: boolean;
		file_upload?: boolean;
		web_search?: boolean;
		image_generation?: boolean;
		code_interpreter?: boolean;
		usage?: boolean;
		citations?: boolean;
		b1_app_access?: boolean;
		subsidie_app_access?: boolean;
		general_chat_app_access?: boolean;
		[key: string]: boolean | undefined;
	} = {};
</script>

<div>
	<div class="flex w-full justify-between mb-1">
		<div class=" self-center text-sm font-semibold">{i18n?.t?.('Capabilities') || 'Capabilities'}</div>
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
						{capabilityLabels[capability].label}
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