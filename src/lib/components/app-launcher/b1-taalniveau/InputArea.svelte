<script>
  export let value;
</script>

<div>
  <textarea
    class="w-full h-48 p-2 border rounded"
    bind:value
    placeholder="Plak hier een tekst of upload een bestand..."
  ></textarea>
</div>

<style>
  textarea {
    resize: none; /* Zet uitschakeling van rescaling textarea */
  }
</style>