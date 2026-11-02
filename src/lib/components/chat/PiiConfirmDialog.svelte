<script lang="ts">
	// GovChat-NL: pop-up van het persoonsgegevensfilter vóór het versturen
	import { createEventDispatcher } from 'svelte';

	import Modal from '$lib/components/common/Modal.svelte';
	import Checkbox from '$lib/components/common/Checkbox.svelte';
	import { PII_CATEGORY_LABELS, PII_SPECIAL_LABELS, type PiiDetection } from '$lib/apis/pii';

	const dispatch = createEventDispatcher();

	export let show = false;
	export let detection: PiiDetection | null = null;

	// Indexen van treffers die de gebruiker heeft uitgevinkt
	let excluded: number[] = [];
	let lastDetection: PiiDetection | null = null;

	$: if (detection !== lastDetection) {
		lastDetection = detection;
		excluded = [];
	}

	$: maskable = (detection?.findings ?? []).filter((f) => f.maskable);
	$: special = (detection?.findings ?? []).filter((f) => !f.maskable);
	$: specialTypes = [...new Set(special.map((f) => f.detail ?? ''))].filter(Boolean);
	$: selectedCount = maskable.filter((f) => !excluded.includes(f.index)).length;

	const toggle = (index: number, checked: boolean) => {
		excluded = checked ? excluded.filter((i) => i !== index) : [...excluded, index];
	};

	// Sluiten via Escape of klikken naast de pop-up telt als "Terug naar bericht"
	let wasShown = false;
	let acted = false;
	$: if (show) {
		wasShown = true;
	} else if (wasShown) {
		wasShown = false;
		if (!acted) {
			dispatch('cancel', { exclude: excluded });
		}
		acted = false;
	}

	const close = (action: 'mask' | 'send' | 'cancel') => {
		acted = true;
		show = false;
		dispatch(action, { exclude: excluded });
	};
</script>

<Modal size="md" bind:show>
	<div class="px-5 py-5 flex flex-col gap-3 dark:text-gray-200" data-testid="pii-dialog">
		<div>
			<div class="text-lg font-medium">Weet je zeker dat je dit wil delen?</div>
			<div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
				Je bericht bevat persoonsgegevens. Deel alleen wat echt nodig is. Je kunt de gegevens eruit
				filteren: ze worden dan vervangen door een label, zoals [BSN] of [NAAM 1].
			</div>
		</div>

		{#if detection}
			<div
				class="text-sm rounded-xl bg-gray-50 dark:bg-gray-850 px-3 py-2 max-h-48 overflow-y-auto whitespace-pre-wrap break-words"
			>
				{#each detection.segments as segment}
					{#if segment.finding !== undefined && detection.findings[segment.finding]?.maskable}
						<mark
							class="rounded px-0.5 {excluded.includes(segment.finding)
								? 'bg-transparent underline decoration-dotted'
								: 'bg-amber-200 dark:bg-amber-700/60 dark:text-white'}">{segment.text}</mark
						>
					{:else if segment.finding !== undefined}
						<span class="underline decoration-wavy decoration-red-400">{segment.text}</span>
					{:else}
						{segment.text}
					{/if}
				{/each}
			</div>
		{/if}

		{#if maskable.length > 0}
			<div>
				<div class="text-sm font-medium mb-1">Gevonden persoonsgegevens</div>
				<div class="flex flex-col gap-1 max-h-48 overflow-y-auto">
					{#each maskable as finding (finding.index)}
						<label class="flex items-center gap-2 text-sm cursor-pointer" data-testid="pii-finding">
							<Checkbox
								state={excluded.includes(finding.index) ? 'unchecked' : 'checked'}
								on:change={(e) => toggle(finding.index, e.detail === 'checked')}
							/>
							<span class="text-gray-500 dark:text-gray-400 shrink-0"
								>{PII_CATEGORY_LABELS[finding.category] ?? finding.category}:</span
							>
							<span class="font-mono truncate">{finding.text}</span>
						</label>
					{/each}
				</div>
				<div class="text-xs text-gray-500 mt-1">
					Vink een gegeven uit als het geen persoonsgegeven is, of als je het bewust wilt delen.
				</div>
			</div>
		{/if}

		{#if specialTypes.length > 0}
			<div
				class="text-sm rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 px-3 py-2"
				data-testid="pii-special"
			>
				<span class="font-medium">Let op: mogelijk bijzondere persoonsgegevens</span>
				({specialTypes.map((t) => PII_SPECIAL_LABELS[t] ?? t).join(', ')}). Deze gegevens zijn extra
				beschermd en worden niet automatisch gefilterd. Pas je bericht aan als dit over een
				herkenbaar persoon gaat.
			</div>
		{/if}

		<div class="flex flex-col sm:flex-row gap-1.5 mt-1">
			<button
				class="text-sm bg-gray-100 hover:bg-gray-200 text-gray-800 dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-white w-full py-2 rounded-full transition"
				type="button"
				data-testid="pii-cancel"
				on:click={() => close('cancel')}
			>
				Terug naar bericht
			</button>
			<button
				class="text-sm bg-gray-100 hover:bg-gray-200 text-gray-800 dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-white w-full py-2 rounded-full transition"
				type="button"
				data-testid="pii-send"
				on:click={() => close('send')}
			>
				Toch versturen
			</button>
			{#if maskable.length > 0}
				<button
					class="text-sm bg-gray-900 hover:bg-gray-800 text-gray-100 dark:bg-gray-100 dark:hover:bg-white dark:text-gray-800 w-full py-2 rounded-full transition disabled:opacity-50"
					type="button"
					data-testid="pii-mask"
					disabled={selectedCount === 0}
					on:click={() => close('mask')}
				>
					Filter eruit en verstuur
				</button>
			{/if}
		</div>
	</div>
</Modal>
