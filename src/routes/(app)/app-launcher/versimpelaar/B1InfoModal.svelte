<script lang="ts">
    import { getContext } from 'svelte';
    import { config, settings } from '$lib/stores';
    import { updateUserSettings } from '$lib/apis/users';
    import Modal from '$lib/components/common/Modal.svelte';

    const i18n = getContext('i18n');
    export let show = false; // Controlled by parent component

    const defaultConfigContent = {
        title: 'Welkom bij B1 Taalniveau',
        introduction:
            'B1 is een taalniveau binnen het Europees Referentiekader (ERK). Teksten op B1-niveau zijn:',
        points: [
            'Helder en eenvoudig geschreven',
            'Geschikt voor mensen met basiskennis van de taal',
            'Makkelijk te begrijpen voor een breed publiek'
        ],
        conclusion:
            'Met deze app kunt u controleren of uw teksten voldoen aan het B1-taalniveau en krijgt u suggesties voor verbetering.'
    };

    $: b1Content = $config?.customization?.b1_info?.content || defaultConfigContent;
    $: currentB1Version = $config?.customization?.b1_info?.version || 1;

    function handleDismiss() {
        localStorage.b1InfoAcknowledgedVersion = String(currentB1Version);
        show = false;
    }

    async function handleAcknowledge() {
        localStorage.b1InfoAcknowledgedVersion = String(currentB1Version);

        if ($settings) {
            await settings.set({ ...$settings, b1InfoAcknowledgedVersion: currentB1Version });
            if (localStorage.token) {
                try {
                    await updateUserSettings(localStorage.token, { ui: $settings });
                } catch (error) {
                    console.error('Failed to update user settings for B1 info:', error);
                }
            }
        }
        show = false;
    }
</script>

<Modal bind:show size="lg" on:close={handleDismiss}>
    <div class="px-5 pt-4 dark:text-gray-300 text-gray-700">
        <div class="flex justify-between items-start">
            <div class="text-xl font-semibold">
                {b1Content.title}
            </div>
            <button class="self-center" on:click={handleDismiss}>
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    class="w-5 h-5"
                >
                    <path
                        d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"
                    />
                </svg>
            </button>
        </div>
    </div>

    <div class="w-full p-4 px-5 text-gray-700 dark:text-gray-100">
        <div class="overflow-y-scroll max-h-96 scrollbar-hidden">
            <div class="mb-6">
                <p class="mb-3">{b1Content.introduction}</p>
                <ul class="list-disc pl-5 space-y-2">
                    {#each b1Content.points as point}
                        <li>{point}</li>
                    {/each}
                </ul>
                <p class="mt-4">{b1Content.conclusion}</p>
            </div>
        </div>
        <div class="flex justify-end pt-3 text-sm font-medium">
            <button
                on:click={handleAcknowledge}
                class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full"
            >
                <span class="relative">{$i18n.t('Begrepen')}</span>
            </button>
        </div>
    </div>
</Modal>