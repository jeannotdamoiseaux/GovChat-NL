<script lang="ts">
	import B1Logic from '$lib/components/app-launcher/b1-taalniveau/b1-logic.svelte';
	import Template from '$lib/components/app-launcher/page-template/template.svelte';
  </script>
  
  <!-- Content Slot -->
  <Template>
	<div slot="content" class="pt-6">
	  <B1Logic />
	</div>
</Template>