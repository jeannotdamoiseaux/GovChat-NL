<script lang="ts">
	import Lechat from '$lib/components/chat/lechat.svelte';
	import B1Logic from '$lib/components/app-launcher/b1-taalniveau/b1-logic.svelte';
	
	let lechatComponent;
</script>

<!-- Content Slot -->
<Lechat bind:this={lechatComponent}>
	<div slot="content" class="pt-16" let:selectedModels>
		<div class="max-w-7xl mx-auto">
            <B1Logic {selectedModels} />
        </div>
	</div>
</Lechat>
