import type { HelpSection, HelpContent } from './HelpContent';

export const helpContent: HelpContent = {
    title: 'Handleiding {{APP_NAME}}',
    subtitle: 'Stel je vragen gerust ook direct aan {{APP_NAME}} — de chatbot kent deze handleiding.',
    sections: [
    {
        id: 'sec1',
        emoji: '',
        title: 'Wat is {{APP_NAME}}?',
        content: `<h2 class="help-chapter-title">Wat is {{APP_NAME}}?</h2>`,
        items: [
            {
                id: 'sec1a',
                emoji: '',
                title: 'Over {{APP_NAME}}',
                content: `
                    <div class="text-sm mb-2">
                    {{APP_NAME}} staat voor <b>Generatieve AI MeierijStad</b>. Het is de AI-chatassistent van gemeente Meierijstad, waarmee je via tekst vragen kunt stellen en ondersteuning krijgt bij je werk.
                    </div>
                    <div class="text-sm mb-2">
                    De assistent kan onder andere informatie opzoeken, uitleg geven, teksten samenvatten of herschrijven, en je helpen bij het opstellen van documenten.
                    </div>
                `
            },
            {
                id: 'sec1b',
                emoji: '',
                title: 'Wat kun je ermee?',
                content: `
                    <ul class="list-disc pl-5 space-y-1 text-sm mb-2">
                    <li>Vragen stellen over beleid, procedures, wetgeving en praktische zaken</li>
                    <li>Teksten en documenten samenvatten of herschrijven</li>
                    <li>Voorstellen laten maken, controleren of uitleg vragen</li>
                    <li>Ideeën genereren of brainstormen over een onderwerp</li>
                    <li>Stapsgewijs uitleg krijgen over complexe onderwerpen</li>
                    </ul>
                `
            },
            {
                id: 'sec1c',
                emoji: '',
                title: 'De kennisgrens',
                content: `
                    <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-2 rounded">
                    <b>Let op:</b> De kennis van {{APP_NAME}} reikt tot en met <b>mei 2024</b>.
                    Informatie of gebeurtenissen na die datum zijn niet bekend bij de chatbot en kunnen onjuist of verzonnen zijn ("hallucineren").
                    Controleer altijd het antwoord, vooral bij actuele of zeer specifieke onderwerpen.
                    </div>
                `
            }
        ]
    },
    {
        id: 'sec2',
        emoji: '',
        title: 'Toegang',
        content: `<h2 class="help-chapter-title">Toegang tot {{APP_NAME}}</h2>`,
        items: [
            {
                id: 'sec2a',
                emoji: '',
                title: 'Voorwaarden',
                content: `
                    <div class="text-sm mb-2">
                    Je krijgt toegang tot {{APP_NAME}} na het afronden van de <b>basiscursus AI-geletterdheid</b> in De Samenscholing.
                    Zonder afronding van deze cursus is het niet mogelijk om in te loggen.
                    </div>
                `
            },
            {
                id: 'sec2b',
                emoji: '',
                title: 'Installatie',
                content: `
                    <ul class="list-disc pl-5 space-y-1 text-sm mb-2">
                    <li><b>In je browser:</b> Ga naar de URL van {{APP_NAME}} en log in met je werkaccount.</li>
                    <li><b>Als app op je pc:</b> Voeg {{APP_NAME}} toe via je browser (bijvoorbeeld Microsoft Edge: Instellingen → Apps → Deze site als app installeren).</li>
                    <li><b>Op je telefoon:</b> Open de URL in je browser. Op iPhone via <i>Delen</i> → <i>Zet op beginscherm</i>, op Android via het menu → <i>Toevoegen aan startscherm</i>.</li>
                    </ul>
                `
            }
        ]
    },
    {
        id: 'sec3',
        emoji: '',
        title: 'Spelregels',
        content: `<h2 class="help-chapter-title">Spelregels</h2>`,
        items: [
            {
                id: 'sec3a',
                emoji: '',
                title: 'Richtlijnen',
                content: `
                    <div class="bg-yellow-100 border-l-4 border-yellow-500 p-4 mb-4 rounded">
                        <ol class="list-decimal pl-5 space-y-2 text-sm">
                            <li>
                                <b>Gebruik {{APP_NAME}} voor je werk</b> — niet openbare chatbots zoals ChatGPT of Copilot.
                            </li>
                            <li>
                                <b>Jij bent verantwoordelijk</b> — AI is een hulpmiddel, niet een vervanging voor je eigen oordeel.
                            </li>
                            <li>
                                <b>Controleer altijd de antwoorden</b> — AI kan fouten maken of informatie verzinnen.
                            </li>
                            <li>
                                <b>Deel geen gevoelige informatie met openbare chatbots</b> — de veiligheid daarvan kan niet worden gegarandeerd.
                            </li>
                            <li>
                                <b>Deel geen bijzondere persoonsgegevens</b> — ook niet in {{APP_NAME}}.
                            </li>
                        </ol>
                    </div>
                `
            },
            {
                id: 'sec3b',
                emoji: '',
                title: 'Disclaimer',
                content: `
                    <div class="text-sm mb-2">
                    {{APP_NAME}} is een AI-assistent ter ondersteuning van je werk, maar geen vervanging voor menselijke expertise of besluitvorming.
                    </div>
                `
            }
        ]
    },
    {
        id: 'sec4',
        emoji: '',
        title: 'Aan de slag',
        content: `<h2 class="help-chapter-title">Aan de slag</h2>`,
        items: [
            {
                id: 'sec4a',
                emoji: '',
                title: 'Chatten',
                content: `
                    <div class="text-sm mb-2">
                    Stel je vragen direct in het chatveld. Hoe concreter en specifieker je vraag, hoe beter {{APP_NAME}} je kan helpen.
                    </div>
                `
            },
            {
                id: 'sec4b',
                emoji: '',
                title: 'Bestanden uploaden',
                content: `
                    <div class="text-sm mb-2">
                    Je kunt documenten of afbeeldingen toevoegen aan je chatgesprek via het plusje (<b>+</b>) linksonder in het invoerveld.
                    Handig voor samenvattingen, analyses of toelichtingen op basis van je eigen bestanden.
                    </div>
                `
            },
            {
                id: 'sec4c',
                emoji: '',
                title: 'Tijdelijke chat',
                content: `
                    <div class="text-sm mb-2">
                    Bij een tijdelijke chat wordt het gesprek niet opgeslagen. Zodra je de chat afsluit is alles verwijderd. Gebruik dit voor gevoelige informatie.
                    </div>
                `
            },
            {
                id: 'sec4d',
                emoji: '',
                title: 'Tips voor goede vragen',
                content: `
                    <ul class="list-disc pl-5 space-y-1 text-sm mb-2">
                    <li><b>Wees concreet:</b> Omschrijf duidelijk wat je wilt weten of bereiken.</li>
                    <li><b>Geef context:</b> Deel relevante achtergrondinformatie mee.</li>
                    <li><b>Geef het gewenste formaat aan:</b> Wil je een lijst, tabel, samenvatting of stappenplan?</li>
                    <li><b>Splits complexe vragen op:</b> Stel per deelonderwerp een aparte vraag.</li>
                    <li><b>Vraag door:</b> Stel vervolgvragen als het antwoord niet compleet is.</li>
                    </ul>
                `
            }
        ]
    },
    {
        id: 'sec5',
        emoji: '',
        title: 'Veelgestelde vragen',
        content: `<h2 class="help-chapter-title">Veelgestelde vragen</h2>`,
        items: [
            {
                id: 'sec5a',
                emoji: '',
                title: 'Hoe veilig is {{APP_NAME}}?',
                content: `
                    <div class="text-sm mb-2">
                    {{APP_NAME}} draait binnen een beveiligde omgeving. Alle communicatie wordt vertrouwelijk behandeld en voldoet aan de geldende privacy- en beveiligingsrichtlijnen.
                    </div>
                `
            },
            {
                id: 'sec5b',
                emoji: '',
                title: 'Hoe actueel is de kennis?',
                content: `
                    <div class="text-sm mb-2">
                    {{APP_NAME}} kent informatie tot en met mei 2024. Recentere informatie kan ontbreken of onjuist zijn. Controleer altijd het antwoord.
                    </div>
                `
            },
            {
                id: 'sec5c',
                emoji: '',
                title: 'Is {{APP_NAME}} altijd beschikbaar?',
                content: `
                    <div class="text-sm mb-2">
                    Ja, {{APP_NAME}} is 24 uur per dag, 7 dagen per week beschikbaar.
                    </div>
                `
            },
            {
                id: 'sec5d',
                emoji: '',
                title: 'Mijn vraag wordt geblokkeerd',
                content: `
                    <div class="text-sm mb-2">
                    Soms wordt een vraag geblokkeerd door ingestelde filters. Probeer je vraag anders te formuleren of start een nieuwe chat.
                    </div>
                `
            },
            {
                id: 'sec5e',
                emoji: '',
                title: 'De chat blijft hangen',
                content: `
                    <div class="text-sm mb-2">
                    Druk op <b>F5</b> (browser) of <b>Ctrl+R</b> (app) om te vernieuwen. Op je telefoon: sluit de app en start opnieuw.
                    </div>
                `
            },
            {
                id: 'sec5f',
                emoji: '',
                title: 'Leert {{APP_NAME}} van mijn gesprekken?',
                content: `
                    <div class="text-sm mb-2">
                    Nee. {{APP_NAME}} onthoudt geen informatie uit eerdere gesprekken. Binnen een chatsessie wordt de gesprekshistorie wel bijgehouden.
                    </div>
                `
            }
        ]
    },
    {
        id: 'sec6',
        emoji: '',
        title: 'Hulp en contact',
        content: `<h2 class="help-chapter-title">Hulp en contact</h2>`,
        items: [
            {
                id: 'sec6a',
                emoji: '',
                title: 'Probleem melden',
                content: `
                    <div class="text-sm mb-2">
                    Loop je tegen een probleem aan? Maak een melding via het <b>Topdesk-formulier</b>.
                    </div>
                `
            },
            {
                id: 'sec6b',
                emoji: '',
                title: 'Contactpersonen',
                content: `
                    <div class="text-sm mb-2">
                    Voor vragen over {{APP_NAME}} kun je terecht bij:
                    </div>
                    <ul class="list-disc pl-5 space-y-1 text-sm mb-2">
                    <li><b>Marjolein van Erp</b></li>
                    <li><b>Kevin van Dinther</b></li>
                    </ul>
                `
            }
        ]
    }
]
};
