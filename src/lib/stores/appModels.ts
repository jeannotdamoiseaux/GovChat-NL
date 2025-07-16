//Gochat models store
import { writable, derived } from 'svelte/store';
import { models } from './index';
import { page } from '$app/stores';

// Interface for model capabilities
interface ModelCapabilities {
    general_chat_app_access?: boolean;
    versimpelaar_app_access?: boolean;
    [key: string]: any;
}

// Interface for model info
interface ModelInfo {
    meta?: {
        capabilities?: ModelCapabilities;
        [key: string]: any;
    };
    [key: string]: any;
}

// Interface for model
interface Model {
    id: string;
    name: string;
    info?: ModelInfo;
    [key: string]: any;
}

// Store to track current app context
export const currentAppContext = writable<'chat' | 'versimpelaar'>('chat'); // Default to 'chat' context

// Derived store that filters models based on current app context
export const filteredModels = derived(
    [models, currentAppContext],
    ([$models, $currentAppContext]) => {
        if (!$models || !Array.isArray($models) || $models.length === 0) {
            console.log('[appModels] No models available or models not loaded yet');
            return [];
        }

        const typedModels = $models as Model[];

        switch ($currentAppContext) {
            case 'versimpelaar':
                const versimpelaarModels = typedModels.filter(model => 
                    model && model.info?.meta?.capabilities?.versimpelaar_app_access === true
                );
                console.log('[appModels] Versimpelaar app context - Available models:', {
                    available_models: versimpelaarModels
                });
                return versimpelaarModels;
                
            case 'chat':
            default:
                // Filter models that have chat_app_access capability
                const generalChatModels = typedModels.filter(model => 
                    model && model.info?.meta?.capabilities?.chat_app_access === true
                );

                console.log('[appModels] Chat app context - Available models:', {
                    available_models: generalChatModels
                });
                return generalChatModels;
        }
    }
);

// Utility function to set app context based on route
export function setAppContextFromRoute(route: string) {
    console.log('[appModels] Setting app context for route:', route);
    
    // Only set context for specific app launcher routes, ignore admin and other routes
    if (route && route.includes('/app-launcher/versimpelaar')) {
        console.log('[appModels] Setting context to versimpelaar');
        currentAppContext.set('versimpelaar');
    } else if (route && route.includes('/app-launcher/subsidies')) {
        console.log('[appModels] Setting context to chat'); // Map subsidies to chat for now
        currentAppContext.set('chat');
    } else if (route && (route.includes('/chat') || route === '/(app)' || route === '/(app)/')) {
        // Only set to chat for chat routes and main app route
        console.log('[appModels] Setting context to chat');
        currentAppContext.set('chat');
    }
    // For all other routes (admin, settings, etc.), don't change the context
}