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
    isSelection?: boolean;
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
        const backendUrl = WEBUI_BASE_URL || 'http://localhost:8080';
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
        const backendUrl = WEBUI_BASE_URL || 'http://localhost:8080';
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

export async function deleteOutput(id: string) {
    try {
        // Verwijderen van de backend
        const backendUrl = WEBUI_BASE_URL || 'http://localhost:8080';
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
        const backendUrl = WEBUI_BASE_URL || 'http://localhost:8080';
        
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

// Voeg deze nieuwe functies toe

export async function persistSelection(selection: SubsidyResponse | null): Promise<boolean> {
    if (!selection || !selection.savedId) {
        console.log("Geen geldige selectie om persistent te maken");
        return false;
    }
    
    try {
        const backendUrl = WEBUI_BASE_URL || 'http://localhost:8080';
        const response = await fetch(`${backendUrl}/api/subsidies/select/${selection.savedId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Backend error: ${response.status} - ${errorText}`);
        }
        
        const result = await response.json();
        console.log("Selectie persistent gemaakt:", result);
        return true;
    } catch (error) {
        console.error("Fout bij persistent maken van selectie:", error);
        return false;
    }
}

export async function loadLastSelection(): Promise<SubsidyResponse | null> {
    try {
        const backendUrl = WEBUI_BASE_URL || 'http://localhost:8080';
        const response = await fetch(`${backendUrl}/api/subsidies/selection`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success && result.has_selection) {
            console.log("Laatste selectie geladen:", result.selection);
            
            // Update de store met de geladen selectie
            subsidyStore.update(store => ({
                ...store,
                selectedOutput: result.selection
            }));
            
            return result.selection;
        } else {
            console.log("Geen eerdere selectie gevonden:", result.message);
            return null;
        }
    } catch (error) {
        console.error("Fout bij laden van laatste selectie:", error);
        return null;
    }
}

// Update de setSelectedOutput functie om selecties ook persistent te maken
// VERWIJDER DE OUDE functie definitie van setSelectedOutput en gebruik alleen deze
export function setSelectedOutput(output: SubsidyResponse | null, makePersistent: boolean = false) {
    subsidyStore.update(store => ({
        ...store,
        selectedOutput: output
    }));
    
    // Alleen persistent maken als dat expliciet gevraagd wordt
    if (makePersistent && output && output.savedId) {
        persistSelection(output).catch(error => {
            console.error("Fout bij persistent maken van selectie:", error);
        });
    }
}

export async function saveSelection(selection: SubsidyResponse | null): Promise<SubsidyResponse | null> {
    if (!selection) return null;
    
    try {
        // Bereid de selectie voor met een duidelijke naam
        const selectionToSave = {
            ...selection,
            name: selection.name || `Selectie ${new Date().toLocaleString()}`,
            timestamp: new Date().toISOString(),
            isSelection: true // Deze vlag gebruiken we om aan te geven dat dit een selectie is
        };

        console.log("Opslaan van selectie naar backend:", selectionToSave.name);
        
        // Opslaan in backend via de bestaande API route
        const backendUrl = WEBUI_BASE_URL || 'http://localhost:8080';
        const saveUrl = `${backendUrl}/api/subsidies/save`;
        
        const response = await fetch(saveUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(selectionToSave)
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Backend error: ${response.status} - ${errorText}`);
        }

        const savedData = await response.json();
        console.log("Selectie succesvol opgeslagen in backend, ID:", savedData.id);
        
        // Update de store met het nieuwe ID uit de backend
        const updatedSelection = {
            ...selectionToSave,
            savedId: savedData.id
        };
        
        // Werk de store bij
        subsidyStore.update(store => ({
            ...store,
            selectedOutput: updatedSelection,
            savedOutputs: [...store.savedOutputs, updatedSelection]
        }));
        
        return updatedSelection;
    } catch (error) {
        console.error("Fout bij opslaan van selectie:", error);
        throw error;
    }
}

// Voeg hier de nieuwe functies voor globale selectie toe onder de bestaande functies

export async function loadGlobalSelection(): Promise<SubsidyResponse | null> {
    try {
        const backendUrl = WEBUI_BASE_URL || 'http://localhost:8080';
        const response = await fetch(`${backendUrl}/api/subsidies/global`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success && result.has_global_selection) {
            console.log("Globale selectie geladen van server:", result.selection);
            
            // Update de store met de geladen globale selectie
            subsidyStore.update(store => ({
                ...store,
                selectedOutput: result.selection
            }));
            
            return result.selection;
        } else {
            console.log("Geen globale selectie gevonden:", result.message);
            return null;
        }
    } catch (error) {
        console.error("Fout bij laden van globale selectie:", error);
        return null;
    }
}

export async function setGlobalSelection(selection: SubsidyResponse | null): Promise<boolean> {
    if (!selection || !selection.savedId) {
        console.log("Geen geldige selectie om als globaal in te stellen");
        return false;
    }
    
    try {
        const backendUrl = WEBUI_BASE_URL || 'http://localhost:8080';
        const response = await fetch(`${backendUrl}/api/subsidies/global/set/${selection.savedId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Backend error: ${response.status} - ${errorText}`);
        }
        
        const result = await response.json();
        console.log("Globale selectie ingesteld:", result);
        return true;
    } catch (error) {
        console.error("Fout bij instellen van globale selectie:", error);
        return false;
    }
}

// Initialize the store on import
initializeStore();