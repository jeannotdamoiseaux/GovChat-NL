<script lang="ts">
  import { user } from '$lib/stores';
  import { apps } from '$lib/appList';

  $: visibleApps = apps.filter(app => app.permission($user));
</script>

<div class="flex flex-col justify-end h-full">
  <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
    {#each visibleApps as app}
      <a
        href={app.href}
        class="flex items-center space-x-4 p-4 bg-white dark:bg-gray-800 rounded-lg shadow hover:bg-gray-100 dark:hover:bg-gray-700 transform hover:-translate-y-1 transition duration-150"
      >
        <!-- App-icoon en naam -->
        <div class="text-3xl">{app.icon}</div>
        <div class="text-lg font-medium text-gray-800 dark:text-gray-200">{app.name}</div>
      </a>
    {/each}
  </div>
</div>

<style>
  a {
    transition: all 0.2s ease-in-out;
  }
</style>