//Gochat models store
import { writable, derived } from 'svelte/store';
import { models } from './index';
import { page } from '$app/stores';

// Interface for model capabilities
interface ModelCapabilities {
    b1_app_access?: boolean;
    subsidie_app_access?: boolean;
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
export const currentAppContext = writable<'b1' | 'subsidie' | 'general'>('general');

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
            case 'b1':
                const b1Models = typedModels.filter(model => 
                    model && model.info?.meta?.capabilities?.b1_app_access === true
                );
                console.log('[appModels] B1 app context - Available models:', {
                    total: typedModels.length,
                    b1Accessible: b1Models.length,
                    b1ModelIds: b1Models.map(m => m.id)
                });
                return b1Models;
                
            case 'general':
            default:
                console.log('[appModels] General context - All models available:', typedModels.length);
                return typedModels;
        }
    }
);

// Utility function to set app context based on route
export function setAppContextFromRoute(route: string) {
    console.log('[appModels] Setting app context for route:', route);
    
    // Only set context for specific app launcher routes, ignore admin and other routes
    if (route && route.includes('/app-launcher/b1-taalniveau')) {
        console.log('[appModels] Setting context to b1');
        currentAppContext.set('b1');
    } else if (route && route.includes('/app-launcher/subsidies')) {
        console.log('[appModels] Setting context to subsidie');
        currentAppContext.set('subsidie');
    } else if (route && (route.includes('/chat') || route === '/(app)' || route === '/(app)/')) {
        // Only set to general for chat routes and main app route
        console.log('[appModels] Setting context to general');
        currentAppContext.set('general');
    }
    // For all other routes (admin, settings, etc.), don't change the context
}