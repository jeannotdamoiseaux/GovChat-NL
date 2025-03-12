<script>
  export let value;
</script>

<div>
  <textarea
    class="w-full h-48 p-2 border rounded bg-gray-100"
    readonly
    value={value}
    placeholder="Hier verschijnt de vereenvoudigde tekst..."
  ></textarea>
</div>

<style>
  textarea {
    resize: none;
  }
</style>