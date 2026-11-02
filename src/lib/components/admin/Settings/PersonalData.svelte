<script lang="ts">
	// GovChat-NL: beheerinstellingen van het persoonsgegevensfilter
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';

	import { getPiiConfig, setPiiConfig, PII_CATEGORY_LABELS } from '$lib/apis/pii';

	import Switch from '$lib/components/common/Switch.svelte';
	import Checkbox from '$lib/components/common/Checkbox.svelte';
	import SettingsSelect from '$lib/components/common/SettingsSelect.svelte';
	import AdminSettingRow from './AdminSettingRow.svelte';
	import AdminSettingSection from './AdminSettingSection.svelte';

	export let saveHandler: Function;

	let config: any = null;

	const CATEGORY_DESCRIPTIONS: Record<string, string> = {
		bsn: 'Burgerservicenummer, gecontroleerd met de 11-proef',
		iban: 'Bankrekeningnummer, gecontroleerd met mod-97',
		geboortedatum: 'Datum met een woord als "geboren" of "geb." ervoor',
		naam: 'Persoonsnamen, herkend met een lokaal Nederlands taalmodel',
		email: 'E-mailadressen',
		telefoon: 'Nederlandse en internationale telefoonnummers',
		adres: 'Straat met huisnummer en postcode',
		id_document: 'Paspoort-, ID-kaart-, rijbewijs- en V-nummer (met context)',
		kenteken: 'Nederlandse kentekens',
		creditcard: 'Creditcardnummers, gecontroleerd met Luhn',
		ip_adres: 'IPv4- en IPv6-adressen',
		bijzonder:
			'Signaalwoorden over gezondheid, religie, afkomst, politiek, vakbond, seksuele geaardheid en strafblad (alleen waarschuwing)'
	};

	const toggleCategory = (category: string, checked: boolean) => {
		config.PII_FILTER_CATEGORIES = checked
			? [...new Set([...config.PII_FILTER_CATEGORIES, category])]
			: config.PII_FILTER_CATEGORIES.filter((c: string) => c !== category);
	};

	const submitHandler = async () => {
		const res = await setPiiConfig(localStorage.token, {
			ENABLE_PII_FILTER: config.ENABLE_PII_FILTER,
			PII_FILTER_DEFAULT_MODE: config.PII_FILTER_DEFAULT_MODE,
			PII_FILTER_CATEGORIES: config.PII_FILTER_CATEGORIES
		}).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
		if (res) {
			config = res;
			saveHandler();
		}
	};

	onMount(async () => {
		config = await getPiiConfig(localStorage.token).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
	});
</script>

<form class="flex h-full flex-col justify-between text-sm" on:submit|preventDefault={submitHandler}>
	<h2 class="text-sm font-medium text-gray-900 dark:text-white mb-4">Persoonsgegevens</h2>

	<div class="flex-1 min-h-0 overflow-y-auto scrollbar-hover pr-1.5">
		{#if config}
			<AdminSettingSection title="Persoonsgegevensfilter" first>
				<AdminSettingRow
					label="Persoonsgegevensfilter"
					description="Controleert berichten vóór het versturen op persoonsgegevens. Staat dit uit, dan doet het filter nergens iets, ook niet bij agents of chats waar het is ingesteld."
					let:labelId
				>
					<Switch bind:state={config.ENABLE_PII_FILTER} ariaLabelledbyId={labelId} />
				</AdminSettingRow>

				{#if config.ENABLE_PII_FILTER}
					<AdminSettingRow
						label="Standaardmodus"
						description="Geldt voor chats en agents zonder eigen instelling. Bij 'Altijd filteren' kan een gebruiker het filter niet uitzetten."
						let:labelId
					>
						<SettingsSelect bind:value={config.PII_FILTER_DEFAULT_MODE} aria-labelledby={labelId}>
							<option value="off">Uit (alleen waar ingesteld)</option>
							<option value="warn">Waarschuwen (pop-up)</option>
							<option value="mask">Altijd filteren</option>
						</SettingsSelect>
					</AdminSettingRow>
				{/if}
			</AdminSettingSection>

			{#if config.ENABLE_PII_FILTER}
				<AdminSettingSection title="Wat wordt herkend">
					{#each config.AVAILABLE_CATEGORIES as category}
						<label class="flex items-start gap-2 cursor-pointer">
							<div class="pt-0.5">
								<Checkbox
									state={config.PII_FILTER_CATEGORIES.includes(category) ? 'checked' : 'unchecked'}
									on:change={(e) => toggleCategory(category, e.detail === 'checked')}
								/>
							</div>
							<div class="min-w-0">
								<div class="text-xs text-gray-700 dark:text-gray-300">
									{PII_CATEGORY_LABELS[category] ?? category}
								</div>
								<div class="text-[0.6875rem] text-gray-400 dark:text-gray-600">
									{CATEGORY_DESCRIPTIONS[category] ?? ''}
								</div>
							</div>
						</label>
					{/each}
				</AdminSettingSection>
			{/if}
		{/if}
	</div>

	<div class="flex justify-end pt-6 text-sm font-normal">
		<button
			class="px-3.5 py-1.5 text-sm font-normal bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full"
			type="submit"
		>
			Opslaan
		</button>
	</div>
</form>
