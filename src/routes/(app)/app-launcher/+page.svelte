<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { models } from '$lib/stores';
	
	const i18n = getContext('i18n');
	
	// Eventuele state voor deze pagina
	let pageTitle = "GovChat-NL";
	let pageDescription = "Een AI-oplossing voor Nederlandse overheidsinstanties";
	
	onMount(() => {
		// Initialisatie code indien nodig
		console.log("GovChat-NL pagina geladen");
	});
</script>

<div class="container mx-auto px-4 py-8">
	<div class="max-w-4xl mx-auto">
		<h1 class="text-3xl font-bold mb-4 text-gray-800 dark:text-white">{pageTitle}</h1>
		<p class="text-lg mb-6 text-gray-600 dark:text-gray-300">{pageDescription}</p>
		
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
			<h2 class="text-xl font-semibold mb-4 text-gray-700 dark:text-gray-200">
				{$i18n.t('Welkom bij GovChat-NL')}
			</h2>
			
			<p class="mb-4 text-gray-600 dark:text-gray-300">
				{$i18n.t('Dit platform is ontworpen voor Nederlandse overheidsinstanties, met als doel ondersteuning te bieden bij de implementatie van AI-oplossingen.')}
			</p>
			
			<div class="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
				<div class="bg-blue-50 dark:bg-blue-900/30 p-4 rounded-lg">
					<h3 class="font-medium text-blue-700 dark:text-blue-300 mb-2">
						{$i18n.t('Gebruiksklare oplossingen')}
					</h3>
					<p class="text-sm text-gray-600 dark:text-gray-400">
						{$i18n.t('Het platform fungeert als een veilig alternatief voor openbare chatbots en dure commerciële oplossingen.')}
					</p>
				</div>
				
				<div class="bg-green-50 dark:bg-green-900/30 p-4 rounded-lg">
					<h3 class="font-medium text-green-700 dark:text-green-300 mb-2">
						{$i18n.t('Specifieke AI-toepassingen')}
					</h3>
					<p class="text-sm text-gray-600 dark:text-gray-400">
						{$i18n.t('Applicaties die specifiek zijn ontworpen voor overheidstaken, zoals het vereenvoudigen van teksten naar B1-taalniveau.')}
					</p>
				</div>
				
				<div class="bg-purple-50 dark:bg-purple-900/30 p-4 rounded-lg">
					<h3 class="font-medium text-purple-700 dark:text-purple-300 mb-2">
						{$i18n.t('Geavanceerde beveiligingsopties')}
					</h3>
					<p class="text-sm text-gray-600 dark:text-gray-400">
						{$i18n.t('Veiligheid staat centraal, met integratie van bestaande Identity and Access Management (IAM)-systemen.')}
					</p>
				</div>
				
				<div class="bg-amber-50 dark:bg-amber-900/30 p-4 rounded-lg">
					<h3 class="font-medium text-amber-700 dark:text-amber-300 mb-2">
						{$i18n.t('Aanpasbare implementatie')}
					</h3>
					<p class="text-sm text-gray-600 dark:text-gray-400">
						{$i18n.t('Ontworpen om makkelijk te integreren binnen bestaande IT-omgevingen van overheidsorganisaties.')}
					</p>
				</div>
			</div>
			
			<div class="mt-8 text-center">
				<a 
					href="/app-launcher/b1-taalniveau" 
					class="inline-block bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-lg transition-colors"
				>
					{$i18n.t('Ga naar B1-taalniveau tool')}
				</a>
			</div>
		</div>
	</div>
</div>
