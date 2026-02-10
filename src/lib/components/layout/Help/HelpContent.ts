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

export const defaultSections: HelpSection[] = [
    {
        id: 'sec1',
        emoji: '📖',
        title: 'Introductie',
        content: `
                   <h2 class="help-chapter-title">1️⃣ Introductie</h2>
                   <div class="mt-3 mb-3 text-base font-semibold text-blue-700 flex items-center gap-2">
                     <span>
                       Je kunt deze handleiding op ieder moment openen door rechtsonder op het vraagteken
                       (<span class="inline-block bg-black text-white rounded-full px-2" style="font-size:1rem;">?</span>)
                       te klikken.
                     </span>
                   </div>
                 `,
        items: [
            {
                id: 'sec1a',
                emoji: '🤔',
                title: 'Wat is kunstmatige intelligentie (AI)?',
                content: `
                    <div class="text-sm mb-2">
                    Kunstmatige intelligentie (afgekort: AI) betekent dat computers taken uitvoeren waarvoor normaal gesproken menselijke intelligentie voor nodig is. 
                    Denk aan het begrijpen van tekst, het herkennen van plaatjes, of het voeren van een gesprek.
                    </div>
                `
            },
            {
                id: 'sec1b',
                emoji: '💬',
                title: 'Wat is een AI-chatassistent zoals {{APP_NAME}}?',
                content: `
                    <div class="text-sm mb-2">
                    Een AI-chatassistent is een programma waarmee je met tekst (chat) vragen kunt stellen en hulp krijgt bij verschillende taken. 
                    Zo'n digitale assistent kan informatie opzoeken, uitleg geven, teksten samenvatten, teksten herschrijven of je helpen bij je werk.
                    </div>
                    <div class="text-sm mb-2">
                    {{APP_NAME}} is ontwikkeld door en voor de Provincie Limburg. 
                    Deze chatbot is nu onder de naam GovChat-NL ook beschikbaar voor andere (overheids)organisaties. 
                    Het platform wordt voortdurend aangevuld met nieuwe functies en toepassingen.
                    </div>
                `
            },
            {
                id: 'sec1c',
                emoji: '📅',
                title: 'Belangrijk: De kennisgrens van {{APP_NAME}}',
                content: `
                    <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-2 rounded">
                    <b>Let op:</b> De kennis van {{APP_NAME}} reikt tot en met <b>mei 2024</b>. 
                    Informatie of gebeurtenissen ná die tijd zijn meestal niet bekend bij de chatbot, 
                    of kunnen zelfs (per ongeluk) door de AI worden verzonnen (“hallucineren”).
                    Controleer dus altijd het antwoord, vooral als het om iets heel specifieks of actueels gaat!
                    </div>
                `
            },
            {
                id: 'sec1d',
                emoji: '🔑',
                title: 'Hoe krijg ik toegang tot {{APP_NAME}}?',
                content: `
                    <div class="text-sm mb-2">
                    Je kunt {{APP_NAME}} alleen gebruiken als je een werkaccount hebt van de Provincie Limburg.
                    </div>
                    <ul class="list-disc pl-5 space-y-1 text-sm mb-2">
                    <li><b>Via internet (in je browser):</b> Ga naar de website van {{APP_NAME}} en log in.</li>
                    <li><b>Als app op je pc:</b> Soms is {{APP_NAME}} als app op je computer geïnstalleerd, anders kun je deze toevoegen via je browser (bijvoorbeeld via Microsoft Edge: Instellingen → Apps → Deze site als app installeren).</li>
                    <li><b>Op je telefoon:</b> Open de URL in internetbrowser. Op iPhone via <i>Delen</i> → <i>Zet op beginscherm</i>, op Android via het menu → <i>Toevoegen aan startscherm</i>.</li>
                    </ul>
                `
            },
            {
                id: 'sec1e',
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
                id: 'sec1f',
                emoji: '🤖',
                title: 'Hoe werkt {{APP_NAME}} technisch?',
                content: `
                        <div class="text-sm mb-2">
                        {{APP_NAME}} maakt gebruik van <b>taalmodellen</b>, een vorm van kunstmatige intelligentie (AI) die gericht is op het begrijpen én <b>genereren</b> van natuurlijke taal en tekst.
                        Zulke modellen worden <b>generatieve AI</b> genoemd, omdat ze niet alleen bestaande tekst kunnen analyseren, maar ook zelfstandig nieuwe, samenhangende teksten kunnen maken.
                        Taalmodellen zijn getraind op zeer grote hoeveelheden tekst en leren zo patronen en structuren in taal herkennen.
                        </div>
                        <div class="text-sm mb-2">
                        {{APP_NAME}} gebruikt zo’n taalmodel om op basis van jouw vraag <i>nieuwe</i> teksten te genereren, toelichtingen te schrijven of samenvattingen te maken ter ondersteuning van je werk.
                        </div>
                        <div class="text-sm mb-2">
                        Er bestaan ook generatieve AI-modellen voor het maken van afbeeldingen of video’s, maar <b>{{APP_NAME}} werkt alleen met tekst</b>.
                        </div>
                        <div class="text-xs text-gray-600 mb-2">
                        Let op: het model zoekt niet live op internet, maar gebruikt informatie tot de <b>kennisgrens</b> van mei 2024 
                        (zie de uitleg over de kennisgrens van {{APP_NAME}} hierboven).
                        </div>
                    `
            },
            {
                id: 'sec1g',
                emoji: '💻',
                title: 'Wat kun je allemaal met {{APP_NAME}}?',
                content: `
                    <div class="text-sm mb-2">
                    Een paar voorbeelden:
                    </div>
                    <ul class="list-disc pl-5 space-y-1 text-sm mb-2">
                    <li>Vragen stellen over beleid, procedures, wetgeving en praktische zaken.</li>
                    <li>Teksten en documenten samenvatten of herschrijven.</li>
                    <li>Voorstellen laten maken, controleren of uitleg vragen.</li>
                    <li>Ideeën genereren of brainstormen over een onderwerp.</li>
                    <li>Stapsgewijs uitleg krijgen (“Leg dit eenvoudig uit”).</li>
                    </ul>
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
                                <b>Gebruik {{APP_NAME}}:</b>
                                Omdat we de veiligheid van openbare chatbots niet kunnen garanderen, is de richtlijn om {{APP_NAME}} te gebruiken, tenzij je specifieke redenen hebt om een openbare chatbot te gebruiken en je je bewust bent van de risico’s.
                            </li>
                            <li>
                                <b>Neem zelf verantwoordelijkheid:</b>
                                Je bent zelf verantwoordelijk voor het werk dat je oplevert; AI is een hulpmiddel.
                            </li>
                            <li>
                                <b>Dubbelcheck de antwoorden:</b>
                                AI kan fouten maken; wees daar oplettend op en dubbelcheck je antwoorden om te voorkomen dat je foutieve informatie overneemt.
                            </li>
                            <li>
                                <b>Deel nooit gevoelige informatie met een <span class="font-mono">openbare</span> chatbot:</b>
                                Als organisatie hebben we geen contractuele afspraken met openbare chatbots, waardoor de veiligheid van de informatie die je op deze website zet niet gewaarborgd kan worden.
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
            emoji: '🔄',
            title: 'Chat blijft hangen of laadt niet?',
            content: `
                <div class="bg-blue-50 border-l-4 border-blue-400 p-4 rounded mb-2">
                <div class="font-bold text-blue-700 mb-1 flex items-center">
                    🔄 De chatbot blijft maar laden?
                </div>
                <div class="text-sm mb-2">
                    Soms blijft de chat "hangen" na het stellen van een vraag. Meestal is dit snel op te lossen:
                    <ul class="list-disc pl-5 space-y-1 mt-2">
                    <li><b>In de webbrowser:</b> Druk op <b>F5</b> of klik op de refresh-knop van je browser.</li>
                    <li><b>In de app (laptop):</b> Gebruik <b>Ctrl+R</b> of rechtermuisklik → <i>Vernieuwen</i>.</li>
                    <li><b>In de app (telefoon):</b> Sluit de app helemaal af en start opnieuw.</li>
                    </ul>
                    <div class="mt-2">In vrijwel alle gevallen werkt {{APP_NAME}} daarna weer naar behoren.</div>
                </div>
                </div>
            `
            },
            {
                id: 'sec2g',
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
                    Je kunt eenvoudig één of meer documenten of afbeeldingen toevoegen aan je chatgesprek. Dit is handig als je bijvoorbeeld samenvattingen, analyses of toelichtingen wilt laten maken op basis van jouw bestanden.
                    </div>
                    <div class="text-sm mb-2">
                    Klik hiervoor linksonder in het invoerveld op het plusje (<b>+</b>). Je ziet nu twee opties:
                    <ul class="list-disc pl-5 mt-1">
                        <li><b>Bestanden uploaden:</b> Selecteer één of meerdere documenten of afbeeldingen van je computer om toe te voegen aan de chat.</li>
                        <li><b>Capture:</b> Maak direct een screenshot van (een deel van) je scherm en voeg deze toe aan de chat.</li>
                    </ul>
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
            <li>De broncode is openbaar via <a href="https://github.com/jeannotdamoiseaux/govchat-nl" target="_blank" class="underline">Github</a>.</li>
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
        emoji: '🤖',
        title: 'Wat is LAICA?',
        content: `
            <div class="text-sm mb-2">
            LAICA is de Limburgse AI Chat Assistent, ontwikkeld om medewerkers van Provincie Limburg te ondersteunen bij kennisvragen, informatie, advies en werkzaamheden.
            </div>
        `
        },
        {
        id: 'sec6b',
        emoji: '👥',
        title: 'Voor wie is LAICA bedoeld?',
        content: `
            <div class="text-sm mb-2">
            LAICA is alleen beschikbaar voor medewerkers van de Provincie Limburg.
            </div>
        `
        },
        {
        id: 'sec6c',
        emoji: '🛠️',
        title: 'Waarvoor kan ik LAICA inzetten?',
        content: `
            <div class="text-sm mb-2">
            Je kunt LAICA gebruiken voor kennisvragen, hulp bij rapporten, zoeken naar beleidsinformatie, het opstellen en samenvatten van teksten en nog veel meer.
            </div>
        `
        },
        {
        id: 'sec6d',
        emoji: '🔒',
        title: 'Hoe veilig is het gebruik van LAICA?',
        content: `
            <div class="text-sm mb-2">
            LAICA draait binnen een beveiligde digitale omgeving. Alle communicatie wordt vertrouwelijk behandeld en voldoet aan interne beveiligings- en privacyrichtlijnen. Deel geen bijzondere of gevoelige persoonsgegevens zonder directe noodzaak. 
            </div>
        `
        },
        {
        id: 'sec6e',
        emoji: '🔐',
        title: 'Kan ik vertrouwelijke of privacygevoelige gegevens gebruiken met LAICA?',
        content: `
            <div class="text-sm mb-2">
            LAICA draait binnen een goed beveiligde omgeving van de Provincie Limburg. Communicatie wordt vertrouwelijk behandeld en voldoet aan de interne privacy- en beveiligingsrichtlijnen. Chatgesprekken zijn uitsluitend voor de betreffende gebruiker en beheerder (onder strenge voorwaarden) zichtbaar. Het systeem voldoet aan Nederlandse en Europese regelgeving (DPIA uitgevoerd). De medewerker kan er overigens ook voor kiezen een tijdelijke chat te starten die vervolgens niet inhoudelijk gelogd wordt. 
            </div>
        `
        },
        {
        id: 'sec6f',
        emoji: '📑',
        title: 'Verwerkt en logt LAICA persoonsgegevens?',
        content: `
            <div class="text-sm mb-2">
            Ja, voor goed functioneren worden onder andere naam, gebruikers-ID en chatinhoud verwerkt en gelogd. Dit gebeurt binnen de organisatie en conform AVG-richtlijnen. Alleen jij én, bij zwaarwegende reden, een beheerder kunnen chatgegevens inzien.
            </div>
        `
        },
        {
        id: 'sec6g',
        emoji: '⏳',
        title: 'Hoe actueel is de kennis van LAICA?',
        content: `
            <div class="text-sm mb-2">
            LAICA kent informatie tot en met <b>mei 2024</b>. Recente ontwikkelingen kunnen ontbreken of onjuist zijn. Controleer altijd het antwoord.
            </div>
        `
        },
        {
        id: 'sec6h',
        emoji: '✍️',
        title: 'Kan ik met LAICA ook afbeeldingen of video’s genereren?',
        content: `
            <div class="text-sm mb-2">
            Nee, LAICA is tekstgebaseerd en kan géén afbeeldingen of video’s maken. Je kunt wél afbeeldingen uploaden of via ‘capture’ een screenshot delen om daarover een tekstvraag te stellen.
            </div>
        `
        },
        {
            id: 'sec6i',
            emoji: '🤝',
            title: 'Kun je LAICA met anderen gebruiken in projecten?',
            content: `
                <div class="text-sm mb-2">
                Ja, je kunt LAICA goed gebruiken als assistent binnen projecten, bijvoorbeeld voor het opzoeken van wetgeving, het genereren van teksten of het structureren van notulen.
                </div>
                <div class="text-sm mb-2">
                Wil je een chatsessie delen met collega’s? Gebruik de drie puntjes (<b>⋮</b>) rechtsboven in het chatscherm en kies <i>Delen</i> om een gesprek te delen. Zo kun je samen verder werken op basis van dezelfde chatgeschiedenis.
                </div>
                <div class="text-xs text-gray-600 mb-1">
                Tegelijk live samenwerken in één chatvenster is (nog) niet mogelijk.
                </div>
            `
        },
        {
        id: 'sec6j',
        emoji: '🌍',
        title: 'Welke talen ondersteunt LAICA?',
        content: `
            <div class="text-sm mb-2">
            Standaard communiceert LAICA in het Nederlands, maar je kunt eventueel ook in andere talen een vraag stellen.
            </div>
        `
        },
        {
            id: 'sec6k',
            emoji: '💰',
            title: 'Wat zijn de kosten voor het gebruik van LAICA?',
            content: `
                <div class="text-sm mb-2">
                Voor medewerkers van Provincie Limburg is het gebruik van LAICA gratis; het is onderdeel van de digitale dienstverlening.
                </div>
                <div class="text-sm mb-2">
                Op de achtergrond betaalt de organisatie op basis van daadwerkelijk gebruik ("betalen naar gebruik"). De kosten per gebruiker of chat zijn over het algemeen zeer laag.
                </div>
            `
        },
        // FUNCTIONALITEIT & GRENZEN
        {
            id: 'sec6l',
            emoji: '✅',
            title: 'Hoe weet ik of de antwoorden van LAICA betrouwbaar zijn?',
            content: `
                <div class="text-sm mb-2">
                LAICA gebruikt een groot taalmodel dat is getraind op veel verschillende bronnen tot en met mei 2024. Het model geeft doorgaans goede en snelle antwoorden, maar kan fouten maken of details verkeerd interpreteren, vooral bij actuele of zeer specifieke onderwerpen.
                </div>
                <div class="text-sm mb-2">
                Een taalmodel <b>genereert</b> antwoorden op basis van patronen in eerder gelezen teksten, en zoekt niet live op internet. In zeldzame gevallen kan het model informatie verzinnen (“hallucineren”) of iets presenteren dat logisch klinkt, maar feitelijk niet klopt.
                </div>
                <div class="text-sm mb-2">
                Controleer daarom belangrijke of gevoelige informatie altijd zelf met een officiële of betrouwbare bron. Gebruik LAICA als hulpmiddel, niet als enige bron van waarheid.
                </div>
            `
        },
        {
        id: 'sec6m',
        emoji: '⚖️',
        title: 'Geeft LAICA advies bij beleids- of besluitvorming?',
        content: `
            <div class="text-sm mb-2">
            Nee, LAICA adviseert niet over formele besluiten of beleid. Het is een hulpmiddel, geen vervanging voor menselijk oordeel of officiële besluitvorming.
            </div>
        `
        },
        {
        id: 'sec6n',
        emoji: '📆',
        title: 'Kan ik LAICA ook buiten kantooruren gebruiken?',
        content: `
            <div class="text-sm mb-2">
            Ja, LAICA is 24 uur per dag, 7 dagen per week beschikbaar.
            </div>
        `
        },
        {
            id: 'sec6o',
            emoji: '⚡',
            title: 'Wat doe ik als LAICA fouten maakt of verkeerde informatie geeft?',
            content: `
                <div class="text-sm mb-2">
                Je bent altijd zelf verantwoordelijk voor wat je met de antwoorden doet. Controleer informatie daarom goed, zeker bij belangrijke zaken. 
                Het is te verwachten dat LAICA soms fouten maakt of onjuiste antwoorden geeft; dit hoort bij hoe de achterliggende techniek werkt.
                </div>
                <div class="text-sm mb-2">
                Merk je structurele fouten of antwoorden die ongewenst of onacceptabel zijn? Geef dit dan door aan de helpdesk.
                </div>
            `
        },
        {
        id: 'sec6p',
        emoji: '🌱',
        title: 'Leert LAICA van eerdere gesprekken?',
        content: `
            <div class="text-sm mb-2">
            Nee, LAICA onthoudt geen informatie uit eerdere gesprekken. Tijdens een chatsessie onthoudt het wel historie van het gesprek.
            </div>
        `
        },
        {
        id: 'sec6r',
        emoji: '🌳',
        title: 'Wat is de CO₂-afdruk van LAICA?',
        content: `
            <div class="text-sm mb-2">
            De CO₂-uitstoot van LAICA is relatief laag: we schatten ongeveer 2 kg CO₂ per maand bij 1000 gebruikers (dit is ongeveer gelijk aan 15 km rijden met een benzineauto).
            </div>
        `
        },
        // PROCES, GOVERNANCE EN LEERMIDDELEN
        {
        id: 'sec6s',
        emoji: '⚙️',
        title: 'Hoe is de logging en inzage geregeld?',
        content: `
            <div class="text-sm mb-2">
            Chatgesprekken worden gelogd zoals beschreven in het personeelshandboek en na 30 dagen automatisch verwijderd. Alleen jijzelf hebt inzage in deze gesprekken; alleen bij zwaarwegende redenen kan een beheerder meekijken.
            </div>
        `
        },
        {
        id: 'sec6t',
        emoji: '🕵️',
        title: 'Wordt er gecontroleerd op vertrouwelijke informatie in gesprekken?',
        content: `
            <div class="text-sm mb-2">
            Nee, gesprekken worden niet automatisch gefilterd of gemonitord. Alleen de gebruiker ziet de eigen chat; enkel bij zwaarwegend belang kan een beheerder toegang krijgen.
            </div>
        `
        },
        {
        id: 'sec6u',
        emoji: '📚',
        title: 'Kunnen gebruikers zelf kennis toevoegen of delen?',
        content: `
            <div class="text-sm mb-2">
            Ja, je kunt provincie-specifieke informatie of documenten toevoegen (deze zijn alleen voor jou zichtbaar). Centrale kennisbanken worden pas later ingericht i.c.m. duidelijke procesafspraken.
            </div>
        `
        },
        {
        id: 'sec6v',
        emoji: '🚦',
        title: 'Hoe wordt voorkomen dat kennisbanken vervuild raken?',
        content: `
            <div class="text-sm mb-2">
            Centrale kennisbanken worden alleen ingericht als er duidelijke procesafspraken zijn.
            </div>
        `
        },
        {
        id: 'sec6w',
        emoji: '🎓',
        title: 'Hoe blijven medewerkers op de hoogte en getraind?',
        content: `
            <div class="text-sm mb-2">
            Digitale leermiddelen zoals deze handleiding, video’s en microlearnings zijn altijd beschikbaar. Digitale vaardigheden maken deel uit van de Limburg Academie.
            </div>
        `
        },
        {
        id: 'sec6x',
        emoji: '⚖️',
        title: 'Hoe voorkomt LAICA politieke of ideologische bias?',
        content: `
            <div class="text-sm mb-2">
                Het taalmodel van LAICA wordt gestuurd met duidelijke instructies (zogeheten "masterprompt") om antwoorden zo neutraal mogelijk te houden. Ondanks deze technische maatregelen is het niet volledig uit te sluiten dat er toch bias of subjectieve formuleringen ontstaan. Blijf daarom altijd kritisch op de antwoorden van LAICA.
            </div>
        `
        },
        {
        id: 'sec6aa',
        emoji: '💻',
        title: 'Wie kan ik benaderen bij technische problemen met LAICA?',
        content: `
            <div class="text-sm mb-2">
            Neem bij technische problemen of vragen contact op met de helpdesk van Provincie Limburg <a href="mailto:[helpdesk@prvlimburg.nl]" class="underline">[helpdesk@prvlimburg.nl]</a>.
            </div>
        `
        }
    ]
  },
  {
    id: 'sec7',
    emoji: '💡', 
    title: 'Ondersteuning, Contact & Leren',
    content: `<h2 class="help-chapter-title">7️⃣ Hulp & Contact</h2>`,
    items: [
      {
        id: 'sec7a',
        emoji: '🆘',
        title: 'Ondersteuning',
        content: `
          <div class="text-sm mb-1">
            Loop je tegen problemen aan of heb je vragen die deze handleiding niet beantwoordt?
            Neem contact op met de helpdesk door een mail te sturen naar
            <a href="mailto:[helpdesk@prvlimburg.nl]" class="underline">[helpdesk@prvlimburg.nl]</a>.
          </div>
        `
      },
      {
        id: 'sec7b',
        emoji: '💡',
        title: 'Ideeën over doorontwikkeling?',
        content: `
            <div class="text-sm mb-2">
            Heb je wensen, feedback of wil je meedenken over de verdere ontwikkeling van {{APP_NAME}} – zoals extra functionaliteit, integraties of organisatiebrede AI-vraagstukken?<br>
            Neem contact op via
            <a href="mailto:ai@prvlimburg.nl" class="underline font-semibold"
                >ai@prvlimburg.nl</a>.
            <br>
            </div>
        `
      },
      {
       id: 'sec7c',
       emoji: '🎓',
       title: 'Meer leren over AI',
       content: `
            <div class="text-sm mb-2">
                Wil je je verder verdiepen in kunstmatige intelligentie? Volg dan ook de <b>Nationale AI Cursus</b>,
                gratis beschikbaar via Studytube voor medewerkers van Provincie Limburg.<br>
                <a href="https://provincielimburg.studytube.nl/courses/435552/de-nationale-ai-cursus" 
                    target="_blank" 
                    rel="noopener" 
                    class="text-blue-600 underline font-semibold"
                >Bekijk de Nationale AI Cursus op Studytube</a>
            </div>
            <div class="text-sm mt-4">
                Voor vragen kun je contact opnemen met de Limburg Academie via 
                <a href="mailto:Limburgacademie@prvlimburg.nl" class="text-blue-600 underline font-semibold">
                Limburgacademie@prvlimburg.nl
                </a>.
            </div>
        `
      }
    ]
  }
];
// Alias for backwards compatibility
export const sections = defaultSections;
