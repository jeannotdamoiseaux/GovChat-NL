<script lang="ts">
	import Subsidies from '$lib/components/app-launcher/subsidies2/subsidies2.svelte';
	import Lechat from '$lib/components/chat/lechat.svelte';
  </script>
  
  <!-- Content Slot -->
  <Lechat>
	<div slot="content" class="pt-6">
	  <Subsidies />
	</div>
  </Lechat>