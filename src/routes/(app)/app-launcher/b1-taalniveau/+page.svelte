<script lang="ts">
	import B1Logic from '$lib/components/app-launcher/b1-taalniveau/b1-logic.svelte';
	import Lechat from '$lib/components/chat/lechat.svelte';
  </script>
  
  <!-- Content Slot -->
  <Lechat>
	<div slot="content" class="pt-6">
	  <B1Logic />
	</div>
  </Lechat>
  