<script lang="ts">
	import Template from '$lib/components/app-launcher/page-template/template.svelte';
	import AppGrid from '$lib/components/app-launcher/AppGrid.svelte';
</script>

<!-- Content Slot -->
<Template>
	<div slot="content" class="pt-16">
		<div class="max-w-7xl mx-auto">
            <AppGrid />
        </div>
	</div>
</Template>
