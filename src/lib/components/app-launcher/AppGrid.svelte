<script lang="ts">
	import { user, models } from '$lib/stores';
	import { apps } from '$lib/appList';
	import { WEBUI_BASE_URL } from '$lib/constants';

	$: visibleApps = apps.filter((app) => app.permission($user));

	// GovChat-NL: dynamische apps — workspace-modellen met de capability
	// 'app_launcher_entry' verschijnen als eigen tegel. Toegangsrechten lopen
	// automatisch via de model-toegangscontrole: $models bevat alleen modellen
	// die deze gebruiker mag zien.
	$: dynamicApps = ($models ?? []).filter(
		(m) => m?.info?.meta?.capabilities?.app_launcher_entry === true
	);
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

		{#each dynamicApps as model (model.id)}
			<a
				href={`/?model=${encodeURIComponent(model.id)}`}
				class="flex items-center space-x-4 p-4 bg-white dark:bg-gray-800 rounded-lg shadow hover:bg-gray-100 dark:hover:bg-gray-700 transform hover:-translate-y-1 transition duration-150"
			>
				<img
					src={model?.info?.meta?.profile_image_url ?? `${WEBUI_BASE_URL}/static/favicon.png`}
					alt=""
					class="size-9 rounded-full object-cover shrink-0"
					draggable="false"
				/>
				<div class="min-w-0">
					<div class="text-lg font-medium text-gray-800 dark:text-gray-200 truncate">
						{model.name}
					</div>
					{#if model?.info?.meta?.description}
						<div class="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">
							{model.info.meta.description}
						</div>
					{/if}
				</div>
			</a>
		{/each}
	</div>
</div>

<style>
	a {
		transition: all 0.2s ease-in-out;
	}
</style>
