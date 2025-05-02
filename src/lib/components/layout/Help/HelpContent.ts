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
      content: `
        <div class="font-semibold text-base mb-2">1️⃣ Introductie </div>
        <div class="text-sm mb-2 font-semibold">Wat is LAICA?</div>
        <div class="text-sm mb-2">
          LAICA is de Limburgse AI Chat Assistent, speciaal ontwikkeld voor medewerkers van Provincie Limburg. 
          Deze digitale assistent beantwoordt vragen, ondersteunt bij dagelijkse werkzaamheden en helpt je efficiënt informatie op te zoeken.
          Het platform is volop in ontwikkeling. Regelmatig worden er nieuwe functies toegevoegd. 
          Houd het intranet in de gaten voor het laatste nieuws!
          LAICA is ontwikkeld binnen Provincie Limburg en sinds kort onder de naam GovChat-NL ook beschikbaar voor andere (overheids)organisaties.
        </div>
        <div class="text-sm mb-2 font-semibold">Inloggen en toegang</div>
        <ul class="list-disc pl-5 space-y-1 text-sm mb-2">
          Toegang tot LAICA kan alleen met een Provinciaal account (Microsoft Entra ID).
          <li><b>Webbrowser:</b> Ga naar laica.prvlimburg.nl. In de rechterzijbalk op het intranet staat ook een snelkoppeling.</li>
          <li><b>App op je pc:</b> In Citrix standaard geïnstalleerd. Lokaal installeren kan via Microsoft Edge: open LAICA → <i>Instellingen</i> → <i>Apps</i> → <i>Deze site installeren als app</i>.</li>
          <li><b>App op je telefoon:</b> Voorgeïnstalleerd op werktelefoons.</li>
        </ul>
        <div class="text-sm mb-2 font-semibold">Waarom LAICA?</div>
        <ul class="list-disc pl-5 space-y-1 text-sm mb-2">
          <li><b>Privacy:</b> Voor LAICA is een DPIA (Data Protection Impact Assessment) uitgevoerd om de privacy van medewerkers te waarborgen. Opslag van je gegevens verloopt volgens de Nederlandse wet- en regelgeving.</li>
          <li><b>Veiligheid:</b> Leveranciers en systeemcomponenten zijn zorgvuldig geselecteerd en in eigen beheer.</li>
          <li><b>Overheidsspecifieke toepassingen:</b> LAICA gaat AI-functies faciliteren die specifiek zijn ontwikkeld ter ondersteuning van overheidstaken, zoals de B1-app voor het schrijven van teksten in begrijpelijke taal (hierover later meer).</li>
          <li><b>Volledige controle:</b> Instellingen en functies worden intern beheerd en afgestemd op de behoeften van medewerkers.</li>
        </ul>
        <div class="text-sm mb-2 font-semibold">Wat zijn taalmodellen?</div>
        <div class="text-sm mb-2">
          Taalmodellen zijn een vorm van kunstmatige intelligentie (AI) die gericht is op het begrijpen én <b>genereren</b> van natuurlijke taal en tekst.
          Zulke modellen worden 'generatieve AI' genoemd, omdat ze niet alleen teksten analyseren, maar ook zelfstandig nieuwe, samenhangende teksten kunnen maken. 
          Ze zijn getraind op grote hoeveelheden tekst en leren zo patronen en structuren van taal herkennen.
          LAICA maakt gebruik van zo’n taalmodel om op basis van je vraag <i>nieuwe</i> teksten te genereren, toelichtingen te schrijven of samenvattingen te maken ter ondersteuning van je werk.
          Er bestaan ook generatieve AI-modellen voor het maken van afbeeldingen of video’s, maar deze functionaliteit biedt LAICA op dit moment niet.
        </div>
        <div class="text-sm mb-2 font-semibold">Wat is een kennisgrens?</div>
        <div class="text-sm mb-2">
          LAICA's kennis reikt tot en met <b>juni 2024</b>. Informatie die daarna verscheen kent LAICA niet, of kan mogelijk worden verzonnen.
          De teksten waarop het model is getraind zijn tot een bepaald moment verzameld: dat is de <b>kennisgrens</b>.
          Antwoorden van LAICA zijn dus gebaseerd op informatie tot dat moment. 
          Vragen over latere ontwikkelingen kunnen onjuiste of verzonnen antwoorden opleveren (ook wel <b>hallucineren</b> genoemd).
        </div>
      `
    },
    {
      id: 'sec2',
      emoji: '⚠️',
      title: 'Belangrijk om te weten',
      content: `
        <div class="font-semibold text-base mb-2">2️⃣ Belangrijk om te weten</div>
        <div class="text-sm mb-2 font-semibold">Sterke punten van LAICA</div>
        <ul class="list-disc pl-5 space-y-1 text-sm mb-2">
          <li><b>Algemene kennis:</b> Brede kennis van algemene concepten, fungeert als vraagbaak.</li>
          <li><b>Taalvaardigheid:</b> Zeer goed in taal- en tekstverwerking.</li>
          <li><b>Creatief:</b> Denkt mee en genereert ideeën.</li>
          <li><b>Nauwkeurig:</b> Volgt instructies precies op.</li>
          <li><b>Beschikbaarheid:</b> Altijd bereikbaar, ook buiten kantoortijden.</li>
          <li><b>Snelheid:</b> Biedt snelle ondersteuning.</li>
        </ul>
        <div class="text-sm mb-2 font-semibold">Beperkingen</div>
        <ul class="list-disc pl-5 space-y-1 text-sm mb-2">
          <li><b>Beperkte feitelijke kennis:</b> Niet geschikt voor zeer specifieke of specialistische details.</li>
          <li><b>Gebrek aan actuele informatie:</b> Kan geen informatie geven over de meest recente gebeurtenissen (zie de kennisgrens).</li>
          <li><b>Mogelijke onnauwkeurigheden:</b> Antwoorden kunnen soms onvolledig of niet volledig correct zijn.</li>
          <li><b>Pleaser-effect:</b> Kan geneigd zijn met je mee te praten in discussies.</li>
          <li><b>Afhankelijk van input:</b> De kwaliteit van het antwoord hangt af van hoe helder en volledig je vraag is.</li>
          <li><b>Beperkt begrip van context:</b> Mist diepe kennis van de context waarin de vraag gesteld wordt.</li>
          <li><b>Geen verantwoordelijkheid:</b> Eindverantwoording voor het gebruik van antwoorden ligt altijd bij de gebruiker.</li>
        </ul>
        <div class="text-sm mb-2 font-semibold">Privacy & Persoonsgegevens</div>
        <div class="text-sm mb-2">
          <b>Let op:</b> Deel geen bijzondere of gevoelige persoonsgegevens.
        </div>
        <div class="text-sm mb-2 font-semibold">Disclaimer</div>
        <div class="text-sm mb-2">
          LAICA is een AI-assistent ter ondersteuning van je werk, maar géén vervanging voor menselijke expertise of besluitvorming.
        </div>
      `
    },
    {
      id: 'sec3',
      emoji: '🛠️',
      title: 'Aan de slag met LAICA',
      content: `
        <div class="font-semibold text-base mb-2">3️⃣ Aan de slag met LAICA</div>
        <div class="text-sm mb-2 font-semibold">Belangrijkste functies</div>
        <ul class="list-disc pl-5 space-y-1 text-sm mb-2">
          <li><b>Chatveld:</b> Stel je vragen in het tekstvak.</li>
          <li><b>Suggesties:</b> Gebruik voorbeeldvragen (prompts) om sneller te starten.</li>
          <li><b>Bestanden/uploaden:</b> Voeg documenten of screenshots toe aan je chats.</li>
          <li><b>Historie:</b> Bekijk en doorzoek eerdere chats.</li>
          <li><b>Tijdelijke chat:</b> Start een nieuwe chat die nergens wordt opgeslagen (ook niet voor jezelf).</li>
          <li><b>Neem stem op:</b> Neem je vraag op via spraak.</li>
          <li><b>Lees antwoord voor:</b> Laat het antwoord hardop voorlezen.</li>
          <li><b>Kopieer:</b> Kopieer het antwoord eenvoudig naar je klembord.</li>
          <li><b>Deel:</b> Deel je chat met collega's.</li>
          <li><b>Help-knop:</b> Raadpleeg de handleiding of veelgestelde vragen.</li>
        </ul>
      `,
      items: [
        {
          id: 'sec3a',
          emoji: '💬',
          title: 'Chatten & prompts',
          content: `
            <div class="text-sm mb-2">Je kunt direct chatten en allerlei prompts uitproberen. Specifieke instructies geven levert de beste resultaten.</div>
          `
        },
        {
          id: 'sec3b',
          emoji: '📄',
          title: 'Bestanden uploaden',
          content: `
            <div class="text-sm mb-2">Upload eenvoudig documenten of screenshots in de chat, bijvoorbeeld voor samenvattingen of analyse.</div>
          `
        }
      ]
    },
    {
      id: 'sec4',
      emoji: '🔍',
      title: 'Goede vragen stellen',
      content: `
        <div class="font-semibold text-base mb-2">4️⃣ Hoe stel je goede vragen? (Prompting)</div>
        <div class="text-sm mb-2 font-semibold">Tips voor effectief prompten</div>
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
    },
    {
      id: 'sec5',
      emoji: '👩‍💻',
      title: 'Technische achtergrond',
      content: `
        <div class="font-semibold text-base mb-2">5️⃣ Technische achtergrond (voor gevorderde gebruikers)</div>
        <ul class="list-disc pl-5 space-y-1 text-sm mb-2">
          <li>LAICA draait op <b>GPT-4.1</b> als enig taalmodel.</li>
          <li>In de nabije toekomst kunnen er meerdere taalmodellen worden aangeboden (zoals Mistral of Google).</li>
          <li>De broncode is openbaar via <a href="https://github.com/jeannotdamoiseaux/govchat-nl" target="_blank" class="underline">github.com/jeannotdamoiseaux/govchat-nl</a>.</li>
          <li>De implementatie volgt de richtlijnen van Provincie Limburg.</li>
          <li>Koppelingen met andere systemen worden stapsgewijs toegevoegd.</li>
        </ul>
      `
    },
    {
      id: 'sec6',
      emoji: '❓',
      title: 'Veelgestelde vragen (FAQ)',
      content: `
        <div class="font-semibold text-base mb-2">6️⃣ Veelgestelde vragen (FAQ)</div>
        <ul class="list-disc pl-5 space-y-1 text-sm mb-2">
          <li>Kan LAICA juridische adviezen geven?</li>
          <li>Hoe veilig is LAICA?</li>
          <li>Hoe ga ik om met vertrouwelijke informatie?</li>
        </ul>
      `
    },
    {
      id: 'sec7',
      emoji: '💡',
      title: 'Hulp & Contact',
      content: `
        <div class="font-semibold text-base mb-1">7️⃣ Hulp & Contact</div>
        <div class="text-sm mb-1">
          Komen er problemen of heb je vragen die deze handleiding niet beantwoordt?
          Neem contact op met de helpdesk of stuur een e-mail naar 
          <a href="mailto:[e-mailadres verborgen]" class="underline">[e-mailadres verborgen]</a>.
        </div>
      `
    }
  ];