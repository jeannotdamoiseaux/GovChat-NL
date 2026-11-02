<script lang="ts">
	import { getContext, onDestroy, onMount } from 'svelte';
	import { getFileChunks, type FileChunks } from '$lib/apis/files';
	import Spinner from '$lib/components/common/Spinner.svelte';

	export let fileId: string;

	const i18n = getContext<any>('i18n');

	let data: FileChunks | null = null;
	let loading = true;
	let error = '';
	let controller: AbortController;

	const load = async () => {
		controller?.abort();
		controller = new AbortController();
		const signal = controller.signal;
		loading = true;
		error = '';
		try {
			const result = await getFileChunks(localStorage.token, fileId, signal);
			if (!signal.aborted) data = result;
		} catch (e) {
			if (!signal.aborted) error = e instanceof Error ? e.message : String(e);
		} finally {
			if (!signal.aborted) loading = false;
		}
	};

	const isBoundary = (char: string | undefined) => char === undefined || /\s/.test(char);
	// Splitters overlap by whole words or lines: the longest start of `text`
	// that the previous chunk ends with, cut at whitespace on both sides.
	const overlapLength = (prev: string, text: string) => {
		for (let length = Math.min(prev.length, text.length); length > 0; length--)
			if (
				isBoundary(text[length]) &&
				isBoundary(prev[prev.length - length - 1]) &&
				prev.endsWith(text.slice(0, length))
			)
				return length;
		return 0;
	};

	$: chunks = (data?.chunks ?? []).map((chunk, i, all) => ({
		...chunk,
		overlap: i ? overlapLength(all[i - 1].text, chunk.text) : 0
	}));
	$: settings = data?.settings;
	// Token splitters measure chunk_size in tokens, so only characters compare to it directly.
	$: showFill = settings?.text_splitter === 'character';
	$: averageLength = chunks.length
		? Math.round(chunks.reduce((sum, chunk) => sum + chunk.text.length, 0) / chunks.length)
		: 0;

	onMount(load);
	onDestroy(() => controller?.abort());
</script>

{#if loading}
	<div class="p-4"><Spinner className="size-4" /></div>
{:else if error}
	<div class="p-4 text-xs">
		<p role="alert">{error}</p>
		<button type="button" on:click={load}>{$i18n.t('Retry')}</button>
	</div>
{:else if settings}
	<div class="flex min-h-0 flex-1 flex-col">
		<div
			class="flex shrink-0 flex-wrap items-center gap-x-3 gap-y-1 border-b border-gray-100 px-3 py-2 text-xs text-gray-500 dark:border-gray-850"
		>
			<span class="text-gray-900 dark:text-gray-100"
				>{$i18n.t('{{COUNT}} chunks', { COUNT: chunks.length })}</span
			>
			{#if chunks.length}
				<span>{$i18n.t('avg. {{COUNT}} characters', { COUNT: averageLength })}</span>
			{/if}
			<span
				>{$i18n.t('Splitter')}: {settings.text_splitter} · {settings.chunk_size} / {settings.chunk_overlap}
				{$i18n.t('overlap')}</span
			>
			{#if settings.markdown_header_splitter}
				<span>{$i18n.t('settings.admin.documents.markdownHeaderTextSplitter.label')}</span>
			{/if}
			<span>{$i18n.t('Extraction')}: {settings.content_extraction_engine}</span>
		</div>

		{#if !chunks.length}
			<p class="px-3 py-4 text-xs text-gray-500">
				{settings.bypass_embedding_and_retrieval
					? $i18n.t(
							'Embedding and retrieval are bypassed, so files are sent to the model in full and no chunks are stored.'
						)
					: $i18n.t('No chunks found. The file may still be processing or has not been indexed.')}
			</p>
		{:else}
			<ol class="min-h-0 flex-1 space-y-2 overflow-y-auto p-3">
				{#each chunks as chunk, i}
					<li class="rounded-xl border border-gray-100 dark:border-gray-850">
						<div
							class="flex items-center gap-2 border-b border-gray-100 px-3 py-1.5 text-xs text-gray-500 dark:border-gray-850"
						>
							<span class="font-mono text-gray-900 dark:text-gray-100">#{i + 1}</span>
							<span>{$i18n.t('{{COUNT}} characters', { COUNT: chunk.text.length })}</span>
							{#if chunk.page !== null}
								<span>{$i18n.t('Page')} {chunk.page + 1}</span>
							{/if}
							{#if showFill}
								<div
									class="ml-auto h-1 w-16 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800"
									title={$i18n.t('Size relative to chunk size')}
								>
									<div
										class="h-full bg-gray-400 dark:bg-gray-500"
										style="width: {Math.min(100, (chunk.text.length / settings.chunk_size) * 100)}%"
									/>
								</div>
							{/if}
						</div>
						<pre
							class="whitespace-pre-wrap break-words px-3 py-2 font-mono text-xs leading-relaxed text-gray-800 dark:text-gray-200">{#if chunk.overlap}<span
									class="text-gray-400 dark:text-gray-500"
									title={$i18n.t('Overlap with previous chunk')}
									>{chunk.text.slice(0, chunk.overlap)}</span
								>{/if}{chunk.text.slice(chunk.overlap)}</pre>
					</li>
				{/each}
			</ol>
		{/if}
	</div>
{/if}
