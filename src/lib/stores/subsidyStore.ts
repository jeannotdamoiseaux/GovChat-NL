import { writable, get } from 'svelte/store';
import type { Writable } from 'svelte/store';
import { WEBUI_BASE_URL } from '$lib/constants';

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
    timestamp?: string;
    name?: string;
}
// --- Einde Interface ---

interface SubsidyStoreData {
    savedOutputs: SubsidyResponse[];
    selectedOutput: SubsidyResponse | null;
    isLoading: boolean;
}

// Initial state
const initialSubsidyData: SubsidyStoreData = {
    savedOutputs: [],
    selectedOutput: null,
    isLoading: false
};

// Create the writable store
export const subsidyStore: Writable<SubsidyStoreData> = writable(initialSubsidyData);

// Initialiseer de store bij startup
export function initializeStore() {
    console.log("Subsidie store initialiseren...");
    subsidyStore.update(store => ({
        ...store,
        savedOutputs: []
    }));
}

// Helper functions to update the store using the API
export async function fetchSavedOutputs() {
    subsidyStore.update(state => ({ ...state, isLoading: true }));
    try {
        // Gebruik ALTIJD expliciete backend URL
        const backendUrl = 'http://localhost:8080';
        console.log("Ophalen van opgeslagen subsidiecriteria van:", backendUrl);
        
        const response = await fetch(`${backendUrl}/api/subsidies/list`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Succesvol ontvangen van backend:", data.length, "items");
        
        subsidyStore.update(store => ({
            ...store,
            savedOutputs: data,
            isLoading: false
        }));
        
        return data;
    } catch (error) {
        console.error("Fout bij ophalen van backend:", error);
        
        subsidyStore.update(state => ({ 
            ...state, 
            isLoading: false 
        }));
        
        return [];
    }
}

export async function addSavedOutput(output: SubsidyResponse) {
    try {
        // Format the output with any missing fields
        const outputToAdd = {
            ...output,
            savedId: output.savedId || crypto.randomUUID(),
            timestamp: output.timestamp || new Date().toISOString(),
            name: output.name || `Subsidie ${new Date().toISOString().slice(0, 16).replace('T', ' ')}`
        };

        console.log("Opslaan subsidiecriterium:", outputToAdd.name);

        // Opslaan in backend
        const backendUrl = 'http://localhost:8080';
        const saveUrl = `${backendUrl}/api/subsidies/save`; 
        
        console.log("API call naar:", saveUrl);
        
        const response = await fetch(saveUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(outputToAdd)
        });

        console.log("API response status:", response.status);
        
        if (response.ok) {
            const savedData = await response.json();
            outputToAdd.savedId = savedData.id;
            console.log("Backend opslag succesvol, ID:", savedData.id);
            
            // Update de store met de nieuwe data
            subsidyStore.update(store => {
                const newOutputs = [...store.savedOutputs, outputToAdd];
                return {
                    ...store,
                    savedOutputs: newOutputs
                };
            });
            
            return { id: outputToAdd.savedId, success: true };
        } else {
            const errorText = await response.text().catch(() => "Kon error tekst niet lezen");
            console.warn(`Backend gaf error ${response.status}:`, errorText);
            throw new Error(`Backend error: ${response.status} - ${errorText}`);
        }
    } catch (error) {
        console.error("Error saving output:", error);
        throw error;
    }
}

export function setSelectedOutput(output: SubsidyResponse | null) {
    subsidyStore.update(store => ({
        ...store,
        selectedOutput: output
    }));
}

export async function deleteOutput(id: string) {
    try {
        // Verwijderen van de backend
        const backendUrl = 'http://localhost:8080';
        const response = await fetch(`${backendUrl}/api/subsidies/${id}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });

        if (response.ok) {
            console.log("Item succesvol verwijderd van backend");
            
            // Update de store
            subsidyStore.update(store => {
                const updatedOutputs = store.savedOutputs.filter(output => output.savedId !== id);
                return {
                    ...store,
                    savedOutputs: updatedOutputs,
                    selectedOutput: store.selectedOutput?.savedId === id ? null : store.selectedOutput
                };
            });
            
            return await response.json();
        } else {
            console.warn("Kon item niet verwijderen van backend:", response.status);
            throw new Error(`Kon item niet verwijderen: ${response.status}`);
        }
    } catch (error) {
        console.error("Error deleting output:", error);
        throw error;
    }
}

export async function clearSavedOutputs() {
    try {
        // Verwijder elk item op de backend
        const currentStore = get(subsidyStore);
        const backendUrl = 'http://localhost:8080';
        
        for (const output of currentStore.savedOutputs) {
            if (output.savedId) {
                await fetch(`${backendUrl}/api/subsidies/${output.savedId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                });
            }
        }
        
        // Wis alles uit de store
        subsidyStore.update(store => ({
            ...store,
            savedOutputs: [],
            selectedOutput: null
        }));
    } catch (error) {
        console.error("Error clearing saved outputs:", error);
        throw error;
    }
}

// Initialize the store on import
initializeStore();