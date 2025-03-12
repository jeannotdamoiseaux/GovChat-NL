<script>
    import Sidebar from '$lib/components/layout/Sidebar.svelte';
    import AppGrid from '$lib/components/app-launcher/AppGrid.svelte';
    import UserMenu from '$lib/components/layout/Sidebar/UserMenu.svelte';
    import MenuLines from '$lib/components/icons/MenuLines.svelte';
    import PencilSquare from '$lib/components/icons/PencilSquare.svelte';
    import { writable } from 'svelte/store';
    import { user } from '$lib/stores';
  
    const showSidebar = writable(true); // Sidebar toggle state
  </script>
  
  <div class="flex h-screen overflow-hidden bg-gray-100 dark:bg-gray-900">
    <!-- Sidebar -->
    {#if $showSidebar}
      <Sidebar />
    {/if}
    
    <!-- Navbar -->
    <header class="navbar">
      <!-- Linkerkant: Sidebar Toggle Knop -->
      <button
        id="sidebar-toggle-button"
        aria-label="Toggle Sidebar"
        class="sidebar-btn"
        on:click={() => showSidebar.set(!$showSidebar)}
      >
        <MenuLines />
      </button>
      
      <!-- Ruimte tussenin (flex-1 duwt knoppen uit elkaar) -->
      <div class="flex-1"></div>
      
      <!-- Nieuwe Chat Knop -->
      <button
        id="new-chat-button"
        aria-label="New Chat"
        class="action-btn"
      >
        <PencilSquare />
      </button>
  
      <!-- User Menu -->
      {#if $user}
        <UserMenu
          class="user-menu flex items-center justify-end"
          role={$user.role}
        >
          <button
            class="user-menu-button select-none flex rounded-xl p-1.5 hover:bg-gray-50 dark:hover:bg-gray-850 transition"
            aria-label="User Menu"
          >
            <img
              src={$user.profile_image_url}
              class="w-10 h-10 object-cover rounded-full"
              alt="User profile"
            />
          </button>
        </UserMenu>
      {/if}
    </header>
  
    <!-- Main Content -->
    <main class="flex-1 p-6 overflow-y-auto">
      <h1 class="text-3xl font-bold text-gray-800 dark:text-gray-200 mb-6">
        App Launcher
      </h1>
      <AppGrid />
    </main>
  </div>
  
  <style>
    /* Algemene layout */
    html, body, div, main {
      margin: 0;
      padding: 0;
      height: 100%;
    }
  
    main {
      overflow-y: auto;
    }
  
    /* Navbar styling */
    .navbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.5rem 1rem;
      background-color: var(--color-bg, #fff);
      color: var(--color-text, #111);
      border-bottom: 1px solid var(--color-border, #e5e7eb);
    }
  
    @media (max-width: 768px) {
      .navbar {
        padding: 0.5rem 0.5rem;
      }
    }
  
    /* Sidebar toggle knop styling */
    .sidebar-btn {
      all: unset; /* Reset standaard knoppen-styles */
      display: flex;
      align-items: center;
      justify-content: center;
      width: 40px;
      height: 40px;
      cursor: pointer;
      border-radius: 0.375rem; /* Licht afgeronde hoekjes */
      transition: background-color 0.2s;
    }
    .sidebar-btn:hover {
      background-color: var(--color-hover, rgba(0, 0, 0, 0.05));
    }
  
    /* Ruimte tussen links/rechts */
    .flex-1 {
      flex: 1; /* Laat de linker- en rechterkanten zich uitspreiden */
    }
  
    /* Nieuwe Chat knop */
    .action-btn {
      all: unset; /* Verwijder standaard button styles */
      display: flex;
      align-items: center;
      justify-content: center;
      width: 40px;
      height: 40px;
      cursor: pointer;
      border-radius: 0.375rem;
      transition: background-color 0.2s;
      margin-right: 0.5rem; /* Extra ruimte rechts van de knop */
    }
    .action-btn:hover {
      background-color: var(--color-hover, rgba(0, 0, 0, 0.05));
    }
  
    /* User Menu */
    .user-menu {
      flex-shrink: 0; /* Zorg dat het gebruikersmenu niet krimpt */
    }
  
    .user-menu-button {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 40px; /* Zorg dat het een consistent formaat heeft */
      height: 40px;
      border-radius: 50%; /* Cirkel voor profielafbeelding */
      transition: background-color 0.2s;
    }
    .user-menu-button:hover {
      background-color: var(--color-hover, rgba(0, 0, 0, 0.05));
    }
  
    .user-menu-button img {
      width: 40px;
      height: 40px;
      object-fit: cover;
      border-radius: 50%; /* Zorg ervoor dat de afbeelding in een cirkel is gesneden */
    }
  </style>