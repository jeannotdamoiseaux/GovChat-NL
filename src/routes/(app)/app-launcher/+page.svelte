<script lang="ts">
	import Lechat from '$lib/components/chat/lechat.svelte';
	import AppGrid from '$lib/components/app-launcher/AppGrid.svelte';
</script>

<!-- Content Slot -->
<Lechat>
	<div slot="content" class="pt-16">
		<div class="max-w-7xl mx-auto">
            <AppGrid />
        </div>
	</div>
</Lechat>
