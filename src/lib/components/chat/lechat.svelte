<script lang="ts">
	import { getContext, onDestroy, onMount, tick } from 'svelte';
	const i18n: Writable<i18nType> = getContext('i18n');

	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { toast } from 'svelte-sonner';

	import { type Unsubscriber, type Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	import { WEBUI_BASE_URL } from '$lib/constants';

	import {
		chatId,
		chats,
		config,
		models,
		settings,
		showSidebar,
		WEBUI_NAME,
		user,
		socket,
		showControls,
		currentChatPage,
		temporaryChatEnabled,
		mobile,
		chatTitle
	} from '$lib/stores';
	
	import {
		copyToClipboard,
		getMessageContentParts,
		createMessagesList
	} from '$lib/utils';

	import { getChatById, getChatList, updateChatById } from '$lib/apis/chats';
	import { getUserSettings } from '$lib/apis/users';

	import Navbar from '$lib/components/chat/Navbar.svelte';
	import Spinner from '../common/Spinner.svelte';

	export let chatIdProp = '';

	let loading = false;
	let messagesContainerElement: HTMLDivElement;
	let navbarElement;
	let chatIdUnsubscriber: Unsubscriber | undefined;

	export let selectedModels = [''];
	let chat = null;
	let history = {
		messages: {},
		currentId: null
	};

	$: if (chatIdProp) {
		(async () => {
			loading = true;
			console.log(chatIdProp);

			if (chatIdProp && (await loadChat())) {
				await tick();
				loading = false;
				window.setTimeout(() => scrollToBottom(), 0);
				const chatInput = document.getElementById('chat-input');
				chatInput?.focus();
			} else {
				await goto('/');
			}
		})();
	}

	const scrollToBottom = async () => {
		await tick();
		if (messagesContainerElement) {
			messagesContainerElement.scrollTop = messagesContainerElement.scrollHeight;
		}
	};

	const loadChat = async () => {
		chatId.set(chatIdProp);
		chat = await getChatById(localStorage.token, $chatId).catch(async (error) => {
			await goto('/');
			return null;
		});

		if (chat) {
			const chatContent = chat.chat;

			if (chatContent) {
				console.log(chatContent);

				selectedModels =
					(chatContent?.models ?? undefined) !== undefined
						? chatContent.models
						: [chatContent.models ?? ''];
				history =
					(chatContent?.history ?? undefined) !== undefined
						? chatContent.history
						: convertMessagesToHistory(chatContent.messages);

				chatTitle.set(chatContent.title);

				const userSettings = await getUserSettings(localStorage.token);
				if (userSettings) {
					await settings.set(userSettings.ui);
				} 

				await tick();
				return true;
			} else {
				return null;
			}
		}
	};

	onMount(async () => {
		console.log('mounted');
		
		if (!$chatId) {
			chatIdUnsubscriber = chatId.subscribe(async (value) => {
				if (!value) {
					await tick(); 
					await initNewChat();
				}
			});
		} else {
			if ($temporaryChatEnabled) {
				await goto('/');
			}
		}

		showControls.subscribe(async (value) => {
			if (!value) {
				// Reset UI states when controls are hidden
			}
		});

		const chatInput = document.getElementById('chat-input');
		chatInput?.focus();
	});

	onDestroy(() => {
		chatIdUnsubscriber?.();
	});

	const initNewChat = async () => {
		// Simplified initialization
		if ($models.length > 0) {
			selectedModels = [$models[0].id];
		}

		history = {
			messages: {},
			currentId: null
		};

		const chatInput = document.getElementById('chat-input');
		setTimeout(() => chatInput?.focus(), 0);
	};
</script>

<svelte:head>
	<title>
		{$chatTitle
			? `${$chatTitle.length > 30 ? `${$chatTitle.slice(0, 30)}...` : $chatTitle} | ${$WEBUI_NAME}`
			: `${$WEBUI_NAME}`}
	</title>
</svelte:head>

<div
    class="h-screen max-h-[100dvh] transition-width duration-200 ease-in-out {$showSidebar
        ? '  md:max-w-[calc(100%-260px)]'
        : ' '} w-full max-w-full flex flex-col"
    id="chat-container"
>
    {#if !loading}
        {#if $settings?.backgroundImageUrl ?? null}
            <div
                class="absolute {$showSidebar ? 'md:max-w-[calc(100%-260px)] md:translate-x-[260px]' : ''} top-0 left-0 w-full h-full bg-cover bg-center bg-no-repeat"
                style="background-image: url({$settings.backgroundImageUrl})  "
            />

            <div
                class="absolute top-0 left-0 w-full h-full bg-linear-to-t from-white to-white/85 dark:from-gray-900 dark:to-gray-900/90 z-0"
            />
        {/if}

        <Navbar
            bind:this={navbarElement}
            chat={{
                id: $chatId,
                chat: {
                    title: $chatTitle,
                    models: selectedModels,
                    system: $settings.system ?? undefined,
                    history: history,
                    timestamp: Date.now()
                }
            }}
            {history}
            title={$chatTitle}
            bind:selectedModels
            shareEnabled={!!history.currentId}
            {initNewChat}
        />
        <slot name="content"></slot>

    {:else if loading}
        <div class="flex items-center justify-center h-full w-full">
            <div class="m-auto">
                <Spinner />
            </div>
        </div>
    {/if}
</div>