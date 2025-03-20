<script>
  export let value;
</script>

<div>
  <textarea
    class="absolute top-0 left-208 w-100 h-131 p-15 border rounded bg-gray-100"
    readonly
    value={value}
    placeholder="


Hier verschijnt de vereenvoudigde tekst..."
  ></textarea>
</div>

<style>
  textarea {
    resize: none;
  }
</style>