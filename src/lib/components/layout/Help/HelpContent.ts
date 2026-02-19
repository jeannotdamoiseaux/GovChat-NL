export interface HelpSection {
    id: string;
    emoji: string;
    title: string;
    content: string;
    items?: {
        id: string;
        emoji: string;
        title: string;
        content: string;
    }[];
}

export interface HelpContent {
    title: string;
    subtitle: string;
    sections: HelpSection[];
}

import { helpContent as limburg } from './HelpContent.limburg';
import { helpContent as meierijstad } from './HelpContent.meierijstad';

const contentSets: Record<string, HelpContent> = { limburg, meierijstad };

export function getHelpContent(contentSet?: string): HelpContent {
    const key = contentSet || 'limburg';
    const available = Object.keys(contentSets);
    const found = key in contentSets;
    console.log(`getHelpContent - requested: "${contentSet}" | resolved key: "${key}" | found: ${found} | available: [${available}]`);
    return contentSets[key] || contentSets['limburg'];
}
