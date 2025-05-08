<script lang="ts">
	import B1Logic from '$lib/components/app-launcher/b1-taalniveau/b1-logic.svelte';
	import Lechat from '$lib/components/chat/lechat.svelte';
	import { onMount } from 'svelte';
	import { user } from '$lib/stores';
	import B1InfoModal from './B1InfoModal.svelte';

	let showFirstTimeInfo = false;

	onMount(() => {
		// Check if this is the first visit
		const hasVisitedB1 = localStorage.getItem('hasVisitedB1App');
		
		if (!hasVisitedB1) {
			// Show info for first-time visitors
			showFirstTimeInfo = true;
			// Mark that they've seen it
			localStorage.setItem('hasVisitedB1App', 'true');
		}
	});

	function closeInfo() {
		showFirstTimeInfo = false;
	}
</script>

{#if showFirstTimeInfo}
	<B1InfoModal on:close={closeInfo} />
{/if}

<Lechat>
	<div slot="content" class="pt-6">
		<B1Logic />
	</div>
</Lechat>