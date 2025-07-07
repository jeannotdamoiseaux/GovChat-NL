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
        if (!$models || $models.length === 0) {
            console.log('[appModels] No models available');
            return [];
        }

        const typedModels = $models as Model[];

        switch ($currentAppContext) {
            case 'b1':
                const b1Models = typedModels.filter(model => 
                    model.info?.meta?.capabilities?.b1_app_access === true
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
    if (route.includes('/app-launcher/b1-taalniveau')) {
        currentAppContext.set('b1');
    } else if (route.includes('/app-launcher/subsidies')) {
        currentAppContext.set('subsidie');
    } else {
        currentAppContext.set('general');
    }
}