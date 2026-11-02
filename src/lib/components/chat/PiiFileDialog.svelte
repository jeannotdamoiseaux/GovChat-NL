<script lang="ts">
	// GovChat-NL: pop-up van het persoonsgegevensfilter na het uploaden van een bestand
	import { createEventDispatcher } from 'svelte';

	import Modal from '$lib/components/common/Modal.svelte';
	import Checkbox from '$lib/components/common/Checkbox.svelte';
	import { PII_CATEGORY_LABELS, PII_SPECIAL_LABELS, type PiiFileDetection } from '$lib/apis/pii';

	const dispatch = createEventDispatcher();

	export let show = false;
	export let fileName = '';
	export let detection: PiiFileDetection | null = null;

	// Indexen van treffers die de gebruiker heeft uitgevinkt
	let excluded: number[] = [];
	let lastDetection: PiiFileDetection | null = null;

	$: if (detection !== lastDetection) {
		lastDetection = detection;
		excluded = [];
	}

	$: maskable = (detection?.findings ?? []).filter((f) => f.maskable);
	$: special = (detection?.findings ?? []).filter((f) => !f.maskable);
	$: specialTypes = [...new Set(special.map((f) => f.detail ?? ''))].filter(Boolean);
	$: hidden = Math.max(0, (detection?.total ?? 0) - (detection?.findings.length ?? 0));
	$: selectedCount = maskable.filter((f) => !excluded.includes(f.index)).length + hidden;

	const toggle = (index: number, checked: boolean) => {
		excluded = checked ? excluded.filter((i) => i !== index) : [...excluded, index];
	};

	// Sluiten via Escape of klikken naast de pop-up telt als "Bestand weghalen"
	let wasShown = false;
	let acted = false;
	$: if (show) {
		wasShown = true;
	} else if (wasShown) {
		wasShown = false;
		if (!acted) {
			dispatch('remove', { exclude: excluded });
		}
		acted = false;
	}

	const close = (action: 'mask' | 'keep' | 'remove') => {
		acted = true;
		show = false;
		dispatch(action, { exclude: excluded });
	};
</script>

<Modal size="md" bind:show>
	<div class="px-5 py-5 flex flex-col gap-3 dark:text-gray-200" data-testid="pii-file-dialog">
		<div>
			<div class="text-lg font-medium">Weet je zeker dat je dit bestand wil delen?</div>
			<div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
				<span class="font-medium text-gray-700 dark:text-gray-300 break-all">{fileName}</span>
				bevat persoonsgegevens. Deel alleen wat echt nodig is. Je kunt de gegevens eruit filteren: ze
				worden dan in de tekst van het bestand vervangen door een label, zoals [BSN] of [NAAM 1]. Het
				taalmodel krijgt alleen die gefilterde tekst te zien.
			</div>
		</div>

		{#if maskable.length > 0}
			<div>
				<div class="text-sm font-medium mb-1">
					Gevonden persoonsgegevens ({maskable.length + hidden})
				</div>
				<div class="flex flex-col gap-1.5 max-h-64 overflow-y-auto">
					{#each maskable as finding (finding.index)}
						<label class="flex items-start gap-2 text-sm cursor-pointer" data-testid="pii-finding">
							<div class="pt-0.5">
								<Checkbox
									state={excluded.includes(finding.index) ? 'unchecked' : 'checked'}
									on:change={(e) => toggle(finding.index, e.detail === 'checked')}
								/>
							</div>
							<div class="min-w-0">
								<div>
									<span class="text-gray-500 dark:text-gray-400"
										>{PII_CATEGORY_LABELS[finding.category] ?? finding.category}:</span
									>
									<span class="font-mono break-all">{finding.text}</span>
								</div>
								<div class="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 break-words">
									…{finding.before}<mark
										class="rounded px-0.5 {excluded.includes(finding.index)
											? 'bg-transparent underline decoration-dotted'
											: 'bg-amber-200 dark:bg-amber-700/60 dark:text-white'}">{finding.text}</mark
									>{finding.after}…
								</div>
							</div>
						</label>
					{/each}
				</div>
				{#if hidden > 0}
					<div class="text-xs text-gray-500 mt-1">
						En nog {hidden} andere treffers verderop in het bestand. Die worden ook gefilterd.
					</div>
				{/if}
				<div class="text-xs text-gray-500 mt-1">
					Vink een gegeven uit als het geen persoonsgegeven is, of als je het bewust wilt delen,
					bijvoorbeeld de naam van een bestuurder in een openbaar stuk.
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
				beschermd en worden niet automatisch gefilterd. Gebruik het bestand niet als het over een
				herkenbaar persoon gaat.
			</div>
		{/if}

		<div class="flex flex-col sm:flex-row gap-1.5 mt-1">
			<button
				class="text-sm bg-gray-100 hover:bg-gray-200 text-gray-800 dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-white w-full py-2 rounded-full transition"
				type="button"
				data-testid="pii-file-remove"
				on:click={() => close('remove')}
			>
				Bestand weghalen
			</button>
			<button
				class="text-sm bg-gray-100 hover:bg-gray-200 text-gray-800 dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-white w-full py-2 rounded-full transition"
				type="button"
				data-testid="pii-file-keep"
				on:click={() => close('keep')}
			>
				Toch gebruiken
			</button>
			{#if maskable.length > 0}
				<button
					class="text-sm bg-gray-900 hover:bg-gray-800 text-gray-100 dark:bg-gray-100 dark:hover:bg-white dark:text-gray-800 w-full py-2 rounded-full transition disabled:opacity-50"
					type="button"
					data-testid="pii-file-mask"
					disabled={selectedCount === 0}
					on:click={() => close('mask')}
				>
					Filter eruit
				</button>
			{/if}
		</div>
	</div>
</Modal>
