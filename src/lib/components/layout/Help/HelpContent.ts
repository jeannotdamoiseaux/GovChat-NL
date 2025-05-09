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

export const sections: HelpSection[] = [
    {
        id: 'sec1',
        emoji: '📖',
        title: 'Introductie',
        content: `<h2 class="help-chapter-title">1️⃣ Introductie</h2>`,
        items: [
            {
                id: 'sec1a',
                emoji: '❓',
                title: 'Wat is {{APP_NAME}}?',
                content: `
                    <div class="text-sm mb-2">
                        {{APP_NAME}} is een AI-chatassistent, ontwikkeld voor de Nederlandse overheid. Deze digitale assistent beantwoordt vragen, ondersteunt bij dagelijkse werkzaamheden en helpt je efficiënt informatie opzoeken.
                        Het platform is volop in ontwikkeling – regelmatig worden er nieuwe functies toegevoegd.
                        {{APP_NAME}} is geïnitieerd door de Provincie Limburg en sinds kort onder de naam GovChat-NL ook beschikbaar voor andere (overheids)organisaties.
                    </div>
                `,
            },
            {
                id: 'sec1b',
                emoji: '🔑',
                title: 'Inloggen en toegang',
                content: `
                    <div class="text-sm mb-2">
                      Toegang tot {{APP_NAME}} is alleen mogelijk met een bevoegd organisatie-account (zoals Microsoft Entra ID).
                    </div>
                    <ul class="list-disc pl-5 space-y-1 text-sm mb-2">
                        <li><b>Webbrowser:</b> Ga naar de URL van {{APP_NAME}}.</li>
                        <li><b>App op je pc:</b> Mogelijk is {{APP_NAME}} standaard geïnstalleerd, of kun je de app lokaal toevoegen via bijvoorbeeld Microsoft Edge: open {{APP_NAME}} → <i>Instellingen</i> → <i>Apps</i> → <i>Deze site installeren als app</i>.</li>
                        <li>
                        <b>App op je telefoon:</b>
                        {{APP_NAME}} is soms al standaard geïnstalleerd. Wil je de app zelf toevoegen aan je smartphone? Open de URL van {{APP_NAME}} in je browser.<br>
                        Op iPhone (Safari): tik op <i>Delen</i> <span title="delen-icoon">(vierkantje met pijltje omhoog)</span> en kies <i>Zet op beginscherm</i>.<br>
                        Op Android (Chrome): open het menu (drie puntjes rechtsboven) en selecteer <i>Toevoegen aan startscherm</i>.
                        </li>
                    </ul>
                `
            },
            {
                id: 'sec1c',
                emoji: '💡',
                title: 'Waarom {{APP_NAME}}?',
                content: `
                    <div class="text-xs italic mb-1">
                        In plaats van openbare of commerciële chatbots zoals ChatGPT of Copilot.
                    </div>
                    <ul class="list-disc pl-5 space-y-1 text-sm mb-2">
                        <li><b>Privacy:</b> Voor {{APP_NAME}} is een DPIA (Data Protection Impact Assessment) uitgevoerd om de privacy van gebruikers te waarborgen. De opslag van je gegevens gebeurt conform de geldende wet- en regelgeving.</li>
                        <li><b>Veiligheid:</b> Leveranciers en systeemcomponenten zijn zorgvuldig geselecteerd en in eigen beheer.</li>
                        <li><b>Overheidsspecifieke toepassingen:</b> {{APP_NAME}} faciliteert AI-functies die zijn ontwikkeld ter ondersteuning van werktaken binnen de publieke sector, zoals een B1-app voor schrijven in begrijpelijke taal (meer hierover volgt).</li>
                        <li><b>Volledige controle:</b> Instellingen en functies worden binnen de organisatie beheerd en afgestemd op de behoeften van gebruikers.</li>
                    </ul>
                `
            },
            {
                id: 'sec1d',
                emoji: '🤖',
                title: 'Wat zijn taalmodellen?',
                content: `
                    <div class="text-sm mb-2">
                        Taalmodellen zijn een vorm van kunstmatige intelligentie (AI) die gericht zijn op het begrijpen én <b>genereren</b> van natuurlijke taal en tekst.
                        Zulke modellen worden 'generatieve AI' genoemd, omdat ze niet alleen teksten kunnen analyseren, maar ook zelfstandig nieuwe, samenhangende teksten kunnen maken. 
                        Ze zijn getraind op grote hoeveelheden tekst en leren zo patronen en structuren van taal herkennen.
                        {{APP_NAME}} maakt gebruik van zo’n taalmodel om op basis van je vraag <i>nieuwe</i> teksten te genereren, toelichtingen te schrijven of samenvattingen te maken ter ondersteuning van je werk.
                        Er bestaan ook generatieve AI-modellen voor het maken van afbeeldingen of video’s, maar deze functionaliteit biedt {{APP_NAME}} op dit moment niet.
                    </div>
                `
            },
            {
                id: 'sec1e',
                emoji: '📅',
                title: 'Wat is een kennisgrens?',
                content: `
                    <div class="text-sm mb-2">
                        De kennis van {{APP_NAME}} reikt tot en met <b>juni 2024</b>. Informatie die daarna verscheen op het internet is mogelijk niet bekend, of kan worden verzonnen.
                        De teksten waarop het model is getraind zijn tot een bepaald moment verzameld: dat is de <b>kennisgrens</b>.
                        Antwoorden van {{APP_NAME}} zijn dus gebaseerd op informatie tot dat moment.
                        Vragen over latere ontwikkelingen kunnen onjuiste of verzonnen antwoorden opleveren (ook wel <b>hallucineren</b> genoemd).
                        Let op: dit betekent niet dat informatie van vóór de kennisgrens altijd correct is!
                    </div>
                `
            }
        ]
    },
    {
        id: 'sec2',
        emoji: '⚠️',
        title: 'Belangrijk om te weten',
        content: `<h2 class="help-chapter-title">2️⃣ Belangrijk om te weten</h2>`,
        items: [
            {
                id: 'sec2a',
                emoji: '📋',
                title: 'Organisatorische richtlijnen voor het gebruik van AI-chatbots',
                content: `
                    <div class="bg-yellow-100 border-l-4 border-yellow-500 p-4 mb-4 rounded">
                        <ol class="list-decimal pl-5 space-y-1 text-sm">
                            <li>
                                <b>Deel nooit gevoelige informatie met een <span class="font-mono">openbare</span> chatbot:</b>
                                Als organisatie hebben we geen contractuele afspraken met openbare chatbots, waardoor de veiligheid van de informatie die je op deze website zet niet gewaarborgd kan worden.
                            </li>
                            <li>
                                <b>Wees zelf de expert:</b>
                                Je bent zelf verantwoordelijk voor het werk dat je oplevert; AI is een hulpmiddel.
                            </li>
                            <li>
                                <b>Dubbelcheck de antwoorden:</b>
                                AI kan fouten maken; wees daar oplettend op en dubbelcheck je antwoorden om te voorkomen dat je foutieve informatie overneemt.
                            </li>
                            <li>
                                <b>Gebruik {{APP_NAME}}:</b>
                                Omdat we de veiligheid van openbare chatbots niet kunnen garanderen, is de richtlijn om {{APP_NAME}} te gebruiken, tenzij je specifieke redenen hebt om een openbare chatbot te gebruiken en je je bewust bent van de risico’s.
                            </li>
                        </ol>
                    </div>
                `
            },
            {
                id: 'sec2b',
                emoji: '⭐',
                title: 'Sterke punten van {{APP_NAME}}',
                content: `
                    <ul class="list-disc pl-5 space-y-1 text-sm mb-2">
                        <li><b>Algemene kennis:</b> Brede kennis van algemene concepten, fungeert als vraagbaak.</li>
                        <li><b>Taalvaardigheid:</b> Zeer goed in taal- en tekstverwerking.</li>
                        <li><b>Creatief:</b> Denkt mee en genereert ideeën.</li>
                        <li><b>Nauwkeurig:</b> Volgt instructies precies op.</li>
                        <li><b>Beschikbaarheid:</b> Altijd bereikbaar, ook buiten kantoortijden.</li>
                        <li><b>Snelheid:</b> Biedt snelle ondersteuning.</li>
                    </ul>
                `
            },
            {
                id: 'sec2c',
                emoji: '🔻',
                title: 'Beperkingen',
                content: `
                    <ul class="list-disc pl-5 space-y-1 text-sm mb-2">
                        <li><b>Beperkte feitelijke kennis:</b> Niet geschikt voor zeer specifieke of specialistische details.</li>
                        <li><b>Gebrek aan actuele informatie:</b> Kan geen informatie geven over de meest recente gebeurtenissen (zie de kennisgrens).</li>
                        <li><b>Mogelijke onnauwkeurigheden:</b> Antwoorden kunnen soms onvolledig of niet volledig correct zijn.</li>
                        <li><b>Pleaser-effect:</b> Kan geneigd zijn met je mee te praten in discussies.</li>
                        <li><b>Afhankelijk van input:</b> De kwaliteit van het antwoord hangt af van hoe helder en volledig je vraag is.</li>
                        <li><b>Beperkt begrip van context:</b> Mist diepe kennis van de context waarin de vraag gesteld wordt.</li>
                        <li><b>Geen verantwoordelijkheid:</b> Eindverantwoordelijkheid voor het gebruik van antwoorden ligt altijd bij de gebruiker.</li>
                    </ul>
                `
            },
            {
                id: 'sec2d',
                emoji: '🛡️',
                title: 'Privacy & Persoonsgegevens',
                content: `
                    <div class="text-sm mb-2">
                        <b>Let op:</b> Deel geen bijzondere of gevoelige persoonsgegevens.
                    </div>
                `
            },
            {
                id: 'sec2e',
                emoji: '🚫',
                title: 'Foutmeldingen en geblokkeerde vragen',
                content: `
                    <div class="bg-red-50 border-l-4 border-red-400 p-4 rounded mb-2">
                      <div class="font-bold text-red-600 mb-1 flex items-center">
                        🚫 BadRequestError · ContentPolicyViolationError
                      </div>
                      <div class="text-sm mb-2 text-red-700">
                        Soms kun je een foutmelding krijgen, bijvoorbeeld <b>ContentPolicyViolationError</b>. 
                        Dit betekent dat jouw vraag, of een deel ervan, is geblokkeerd door de ingestelde filters.
                      </div>
                      <div class="text-sm mb-2">
                        Deze filters beschermen tegen vragen over ongepaste onderwerpen, zoals seksueel expliciete of gewelddadige inhoud.
                      </div>
                      <div class="font-semibold mb-1 mt-3">Tip:</div>
                      <ol class="list-decimal pl-5 mb-0">
                        <li>Pas je oorspronkelijke bericht aan (klik op het potlood-icoon onder je vraag).</li>
                        <li>Start een nieuwe chat en probeer het opnieuw.</li>
                      </ol>
                    </div>
                `
            },
            {
                id: 'sec2f',
                emoji: '📝',
                title: 'Disclaimer',
                content: `
                    <div class="text-sm mb-2">
                        {{APP_NAME}} is een AI-assistent ter ondersteuning van je werk, maar géén vervanging voor menselijke expertise of besluitvorming.
                    </div>
                `
            }
        ]
    },
    {
        id: 'sec3',
        emoji: '🛠️',
        title: 'Aan de slag',
        content: `<h2 class="help-chapter-title">3️⃣ Aan de slag met {{APP_NAME}}</h2>`,
        items: [
            {
                id: 'sec3a',
                emoji: '💬',
                title: 'Chatten & prompts',
                content: `
                    <div class="text-sm mb-2">
                        Stel je vragen direct in het chatveld. Je kunt ook gebruikmaken van <b>prompts</b> (voorbeeldvragen) om sneller te starten of inspiratie op te doen.
                        Hoe concreter en specifieker je je vraag of instructie formuleert, hoe beter {{APP_NAME}} je kan helpen.
                    </div>
                `
            },
            {
                id: 'sec3b',
                emoji: '📄',
                title: 'Bestanden uploaden',
                content: `
                    <div class="text-sm mb-2">
                        Voeg eenvoudig documenten of screenshots toe aan je chatgesprek, bijvoorbeeld voor het maken van samenvattingen, analyses of toelichtingen.
                    </div>
                `
            },
            {
                id: 'sec3c',
                emoji: '🕓',
                title: 'Tijdelijke chat & privacy',
                content: `
                    <div class="text-sm mb-2">
                        Bij een tijdelijke chat wordt het gesprek niet opgeslagen, ook niet in onze eigen omgeving. Zodra je de chat afsluit, is de informatie verwijderd en niet meer terug te halen. Dit is de veiligste manier om te werken met gevoelige informatie in {{APP_NAME}}.
                    </div>
                `
            }
        ]
    },
    {
    id: 'sec4',
    emoji: '🔍',
    title: 'Goede vragen stellen',
    content: `<h2 class="help-chapter-title">4️⃣ Hoe stel je goede vragen? (Prompting)</h2>`,
    items: [
      {
        id: 'sec4a',
        emoji: '💡',
        title: 'Tips voor effectief prompten',
        content: `
          <ul class="list-disc pl-5 space-y-1 text-sm mb-2">
            <li><b>Wees duidelijk en volledig:</b> Omschrijf zo concreet mogelijk wat je wilt weten...</li>
            <li><b>Geef relevante achtergrondinformatie:</b> Lever context zoals beleid, afdelingen, tijdsperiode of doelen...</li>
            <li><b>Vraag om het gewenste antwoordformaat:</b> Geef aan of je een lijst, tabel, samenvatting of stappenplan wilt.</li>
            <li><b>Splits complexe vragen op:</b> Stel voor elk deelonderwerp een aparte vraag en werk stapsgewijs.</li>
            <li><b>Gebruik voorbeelden:</b> Geef een voorbeeld van het gewenste resultaat.</li>
            <li><b>Benadruk wat belangrijk is:</b> Vertel waar de focus op moet liggen.</li>
            <li><b>Vraag om een stapsgewijze uitleg:</b> Vraag “Beschrijf stap voor stap hoe het proces verloopt”.</li>
            <li><b>Stel vervolgvragen:</b> Vraag door of verduidelijk als het antwoord niet compleet is.</li>
          </ul>
        `
      }
    ]
  },
  {
    id: 'sec5',
    emoji: '👩‍💻',
    title: 'Technische achtergrond',
    content: `<h2 class="help-chapter-title">5️⃣ Technische achtergrond (voor gevorderde gebruikers)</h2>`,
    items: [
      {
        id: 'sec5a',
        emoji: '🧠',
        title: 'Over het model en techniek',
        content: `
          <ul class="list-disc pl-5 space-y-1 text-sm mb-2">
            <li>{{APP_NAME}} draait op <b>GPT-4.1</b> als enig taalmodel.</li>
            <li>In de nabije toekomst kunnen er via {{APP_NAME}} meerdere taalmodellen worden aangeboden (zoals Mistral of Gemini).</li>
            <li>De broncode is openbaar via <a href="https://github.com/jeannotdamoiseaux/govchat-nl" target="_blank" class="underline">github.com/jeannotdamoiseaux/govchat-nl</a>.</li>
            <li>De implementatie volgt de richtlijnen van Provincie Limburg.</li>
            <li>Koppelingen met andere systemen worden stapsgewijs toegevoegd.</li>
          </ul>
        `
      }
    ]
  },
  {
    id: 'sec6',
    emoji: '❓',
    title: 'Veelgestelde vragen (FAQ)',
    content: `<h2 class="help-chapter-title">6️⃣ Veelgestelde vragen (FAQ)</h2>`,
    items: [
      {
        id: 'sec6a',
        emoji: '⚖️',
        title: 'Kan {{APP_NAME}} juridische adviezen geven?',
        content: `<div class="text-sm mb-2">Kan {{APP_NAME}} juridische adviezen geven?</div>`
      },
      {
        id: 'sec6b',
        emoji: '🔒',
        title: 'Hoe veilig is {{APP_NAME}}?',
        content: `<div class="text-sm mb-2">Hoe veilig is {{APP_NAME}}?</div>`
      },
      {
        id: 'sec6c',
        emoji: '🔐',
        title: 'Hoe ga ik om met vertrouwelijke informatie?',
        content: `<div class="text-sm mb-2">Hoe ga ik om met vertrouwelijke informatie?</div>`
      }
    ]
  },
  {
    id: 'sec7',
    emoji: '💡', 
    title: 'Hulp & Contact',
    content: `<h2 class="help-chapter-title">7️⃣ Hulp & Contact</h2>`,
    items: [
      {
        id: 'sec7a',
        emoji: '🆘',
        title: 'Contact opnemen',
        content: `
          <div class="text-sm mb-1">
            Loop je tegen problemen aan of heb je vragen die deze handleiding niet beantwoordt?
            Neem contact op met de helpdesk of stuur een e-mail naar
            <a href="mailto:[e-mailadres verborgen]" class="underline">[e-mailadres verborgen]</a>.
          </div>
        `
      }
    ]
  }
];