<script lang="ts">
    import B1Logic from '$lib/components/app-launcher/b1-taalniveau/b1-logic.svelte';
    import Lechat from '$lib/components/chat/lechat.svelte';
    import { onMount, onDestroy } from 'svelte';
    import { config, settings } from '$lib/stores';
    import { currentAppContext } from '$lib/stores/appModels';
    import B1InfoModal from './B1InfoModal.svelte';
    import type { Unsubscriber } from 'svelte/store';

    let showB1InfoModal = false;

    let configUnsubscribe: Unsubscriber | undefined;
    let settingsUnsubscribe: Unsubscriber | undefined;

    function checkModalVisibility(cfg: typeof $config | null, userSettings: typeof $settings | null) {
        if (cfg && userSettings) {
            const currentB1VersionFromConfig = cfg?.customization?.b1_info?.version || 1;
            const acknowledgedVersion = userSettings.b1InfoAcknowledgedVersion || 0;

            console.log('[B1 Page] Checking modal visibility:');
            console.log('[B1 Page] Config B1 Version:', currentB1VersionFromConfig);
            console.log('[B1 Page] User Acknowledged B1 Version:', acknowledgedVersion);

            if (acknowledgedVersion < currentB1VersionFromConfig) {
                showB1InfoModal = true;
                console.log('[B1 Page] Modal should show.');
            } else {
                showB1InfoModal = false;
                console.log('[B1 Page] Modal should NOT show.');
            }
        } else {
            console.warn('[B1 Page] Config or settings not yet available for modal check.');
        }
    }

    onMount(() => {
        // Set app context for B1 app
        currentAppContext.set('b1');
        
        // Initial check with current values (might be null if stores are not ready)
        checkModalVisibility($config, $settings);

        // Subscribe to changes
        configUnsubscribe = config.subscribe((newConfig) => {
            checkModalVisibility(newConfig, $settings);
        });

        settingsUnsubscribe = settings.subscribe((newSettings) => {
            checkModalVisibility($config, newSettings);
        });
    });

    onDestroy(() => {
        // Reset app context when leaving B1 app
        currentAppContext.set('general');
        
        // Unsubscribe to prevent memory leaks
        if (configUnsubscribe) {
            configUnsubscribe();
        }
        if (settingsUnsubscribe) {
            settingsUnsubscribe();
        }
    });
</script>

{#if showB1InfoModal}
    <B1InfoModal bind:show={showB1InfoModal} />
{/if}

<Lechat>
    <div slot="content" class="pt-6">
        <B1Logic />
    </div>
</Lechat>