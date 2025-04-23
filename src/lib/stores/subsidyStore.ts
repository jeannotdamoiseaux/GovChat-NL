import { writable } from 'svelte/store';
import type { Writable } from 'svelte/store';

// --- Interface kopiëren of importeren ---
// Zorg dat deze interface overeenkomt met die in subsidies.svelte
interface SubsidyCriterion {
    id: number;
    text: string;
}
export interface SubsidyResponse {
    criteria: SubsidyCriterion[];
    summary?: string;
    savedId?: string;
    timestamp?: Date;
    name?: string;
}
// --- Einde Interface ---

interface SubsidyStoreData {
    savedOutputs: SubsidyResponse[];
    selectedOutput: SubsidyResponse | null;
}

// Initial state
const initialSubsidyData: SubsidyStoreData = {
    savedOutputs: [],
    selectedOutput: null
};

// Create the writable store
export const subsidyStore: Writable<SubsidyStoreData> = writable(initialSubsidyData);

// Optioneel: Helper functies om de store te updaten
export function addSavedOutput(output: SubsidyResponse) {
    subsidyStore.update(store => {
        // Voeg unieke ID en timestamp toe als ze ontbreken (kan ook in component)
        const outputToAdd = {
            ...output,
            savedId: output.savedId ?? crypto.randomUUID(),
            timestamp: output.timestamp ?? new Date()
        };
        return {
            ...store,
            savedOutputs: [...store.savedOutputs, outputToAdd]
        };
    });
}

export function setSelectedOutput(output: SubsidyResponse | null) {
    subsidyStore.update(store => ({
        ...store,
        selectedOutput: output
    }));
}

export function clearSavedOutputs() {
     subsidyStore.update(store => ({
        ...store,
        savedOutputs: [],
        selectedOutput: null // Reset selectie ook bij wissen
    }));
}