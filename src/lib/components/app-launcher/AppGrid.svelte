<script>
    import { user } from '$lib/stores';
  
    // Lijst van alle beschikbare apps met permissielogica
    let apps = [
      {
        name: 'B1 Taalniveau',
        icon: '🔤',
        href: '/app-launcher/b1-taalniveau',
        permission: (user) => user?.role === 'admin' || user?.permissions?.appLauncher?.b1_taalniveau
      },
      {
        name: 'Subsidies',
        icon: '💰',
        href: '/app-launcher/subsidies',
        permission: (user) => user?.role === 'admin' || user?.permissions?.appLauncher?.subsidies
      },
      {
        name: 'Transcriptie',
        icon: '🎤',
        href: '/app-launcher/transcriptie',
        permission: (user) => user?.role === 'admin' || user?.permissions?.appLauncher?.transcriptie
      },
    ];
  
    // Filter alleen de apps die zichtbaar moeten zijn voor deze gebruiker
    let visibleApps = apps.filter(app => app.permission($user));
  </script>
  
  <!-- UI-template -->
  <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
    {#each visibleApps as app}
      <a
        href={app.href}
        class="flex items-center space-x-4 p-4 bg-white dark:bg-gray-800 rounded-lg shadow hover:bg-gray-100 dark:hover:bg-gray-700 transform hover:-translate-y-1 transition duration-150"
      >
        <!-- Toon het icoon en de naam van de app -->
        <div class="text-3xl">{app.icon}</div>
        <div class="text-lg font-medium text-gray-800 dark:text-gray-200">{app.name}</div>
      </a>
    {/each}
  </div>
  
  <style>
    a {
      transition: all 0.2s ease-in-out;
    }
  </style>