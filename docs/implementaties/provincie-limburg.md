# Documentatie Pilot-Implementatie Provincie Limburg
De Provincie Limburg draait sinds 21 mei 2025 GovChat-NL als de Limburgse AI Chat Assistent (LAICA). Deze documentatie beschrijft de docker-stack en haar configuratie-onderdelen.

## 1. Overzicht van de Componenten
| **Wat**             | **Leverancier**          | **Details**                                    |
|----------------------|--------------------------|------------------------------------------------|
| **Taalmodellen**     | Microsoft Azure          | GPT-4.1, GPT-4o, text-embeddings-3-large  |
| **Virtual Machine**  | Hetzner via Elestio     | Hosting van infrastructuur                    |
| **Authenticatie**    | Microsoft Entra ID       | Single sign-on en beveiligde login            |

## 2. Snelle start
### 2.1 Docker Configuratie

Deze implementatie van LAICA bestaat uit meerdere samenwerkende softwareonderdelen (componenten), die elk als een zelfstandige 'container' via Docker draaien. Docker-onderdelen zijn als volgt opgebouwd, zowel qua concept als inrichting:

#### Wat zijn Docker images en containers?

- **Docker image:**  
  Een Docker image is een kant-en-klaar pakket van software, inclusief alle benodigde instructies, afhankelijkheden en instellingen om die software uit te voeren. Een image wordt één keer gebouwd en kan daarna op iedere geschikte server identiek worden gestart.

- **Container:**  
  Een container is een draaiende (uitgevoerde) instantie van een image. Containers zijn geïsoleerd van elkaar; zo draaien ze onafhankelijk, maar kunnen via netwerken/volumes samenwerken wanneer dat gewenst is.

#### Waarom Docker Compose?

Met **Docker Compose** beheer je meerdere containers als één samenhangend geheel via een configuratiebestand (`docker-compose.yml`). Je beschrijft hierin wélke images worden gebruikt, welke netwerkverbindingen en volumes ze hebben, en met welke instellingen/omgevingvariabelen ze opstarten.  
Dit maakt het opstarten, beheren en opschalen van een multi-component applicatie overzichtelijk en reproduceerbaar.

#### Overzicht van deze componenten

In de stack voor LAICA worden de volgende (open source of publieke) images gebruikt:


| Docker image                                   | Rol / functionaliteit                                    |
|------------------------------------------------|---------------------------------------------------------|
| `ghcr.io/jeannotdamoiseaux/govchat-nl`         | **Webinterface** (OpenWebUI) — de gebruikersinterface van LAICA |
| `ghcr.io/berriai/litellm`                      | **LLM-adapter/router** — koppelt en verdeelt LLM-verzoeken naar taalmodellen. |
| `apache/tika`                                  | **Documentverwerking** — analyseert/extraheert tekst uit documenten voor de chatassistent                      |
| `postgres`                                     | **Database** — slaat gebruikersgegevens, chathistorie en configuratie op       |

#### Werkschema in de praktijk

1. Je configureert in het `.env`-bestand alle benodigde geheime gegevens en afstemmingen (zoals API-sleutels, domeinnamen, wachtwoorden).
2. Met het commando `docker compose up -d` start je alle beschreven containers tegelijk; ze worden automatisch met elkaar verbonden (binnen het eigen Docker-netwerk).
3. Updates (bijvoorbeeld nieuwe versies van LAICA of LiteLLM) breng je door een nieuwe image-versie te pullen en de stack opnieuw te starten.
4. Logs, foutmeldingen en storingen zijn per container afzonderlijk te bekijken, bijvoorbeeld met `docker logs <containernaam>`.

**Belangrijk:**  
Sla gevoelige gegevens zoals wachtwoorden, API-sleutels enzovoort altijd op in een `.env`-bestand dat niet wordt gedeeld buiten de beheerdersgroep.  

#### Voorbeeld: `docker-compose.yml`
```yaml
version: "3.3"

services:
  open-webui:
    image: ghcr.io/jeannotdamoiseaux/govchat-nl:v1.0.0
    restart: always
    ports:
      - 8080:8080
    environment:
    # 1. Authenticatie & security
    - ADMIN_EMAIL=<admin@example.org>               # Admin-login e-mail (hoeft niet te bestaan)
    - ADMIN_PASSWORD=<Password>                     # Wachtwoord voor admin
    - ENV=prod                                      # Omgeving (prod/dev)
    - DOMAIN=<laica.example.org>                    # (Sub)domein van de app
    - WEBUI_SECRET_KEY=<SuperSecret123>             # Geheime sleutel voor sessies/encryptie
    - SAFE_MODE=true                                # Extra beveiliging inschakelen
    - DEFAULT_USER_ROLE="user"                      # Standaardrol nieuw account/SSO
    - JWT_EXPIRES_IN="24h"                          # Token-geldigheid (standaard 24 uur)

    # 2. Microsoft Entra / Azure SSO (OAuth)
    - OAUTH_PROVIDER_NAME=Microsoft                 # Altijd 'Microsoft' voor Entra ID
    - MICROSOFT_CLIENT_ID=<MICROSOFT_CLIENT_ID>     # Azure App/Client ID
    - MICROSOFT_CLIENT_SECRET=<MICROSOFT_CLIENT_SECRET> # Azure Client Secret
    - MICROSOFT_CLIENT_TENANT_ID=<MICROSOFT_CLIENT_TENANT_ID> # Azure Tenant-ID
    - MICROSOFT_REDIRECT_URI=https://laica.example.org/oauth/microsoft/callback # OAuth callback-URL
    - MICROSOFT_OAUTH_SCOPE="openid email profile"  # OAuth scopes/gebruikersrechten
    - ENABLE_OAUTH_GROUP_MANAGEMENT=false           # (Optioneel) Groepsbeheer via Azure
    - ENABLE_OAUTH_SIGNUP=true                      # Nieuwe accounts via SSO toestaan

    # 3. AI-model & API
    - OPENAI_API_BASE_URL="http://litellm:4000"     # Interne URL LiteLLM-router

    # 4. Frontend / UI instellingen
    - WEBUI_NAME="Laica"                            # Naam in interface
    - WEBUI_URL=<https://laica.example.org>         # Publieke webinterface-url
    - ENABLE_SIGNUP=false                           # Lokale signup uitschakelen
    - ENABLE_LOGIN_FORM=false                       # Lokale loginscherm uitschakelen (SSO)
    - EMPTY_CHAT_WELCOME_MESSAGE="Ik ben Laica"     # Welkomsttekst in leeg chatvenster
    - LOGIN_SCREEN_SUBTITLE="Jouw kennisassistent voor de Provincie Limburg" # Ondertitel loginpagina
    - DEFAULT_LOCALE=nl-NL                         # Standaardtaal
    - SHOW_ADMIN_DETAILS=false                      # Admin-details verbergen voor gewone gebruikers

    # 5. Functies & gebruikersrechten
    - ENABLE_ADMIN_CHAT_ACCESS=false                # Beheerder heeft inzage gebruikerschats?
    - ENABLE_CODE_INTERPRETER=false                 # Code interpreter inschakelen?
    - ENABLE_API_KEY=false                          # Inloggen met API-sleutels?
    - ENABLE_COMMUNITY_SHARING=false                # Delen met andere gebruikers?
    - ENABLE_MESSAGE_RATING=false                   # AI-antwoorden beoordelen?
    - ENABLE_EVALUATION_ARENA_MODELS=false          # Modelvergelijking inschakelen?
    - ENABLE_VERSION_UPDATE_CHECK=false             # Automatische updatecheck?
    - ENABLE_CHANNELS=false                         # Groepskanalen/kanalenfunctie?
    - ENABLE_DIRECT_CONNECTIONS=false               # Directe verbindingen tussen gebruikers?
    - ENABLE_USER_WEBHOOKS=false                    # Webhooks voor gebruikers?
    - USER_PERMISSIONS_CHAT_CALL=false              # Voice/video call inschakelen?
    - USER_PERMISSIONS_CHAT_MULTIPLE_MODELS=false   # Meerdere AI-modellen per chat?
    - USER_PERMISSIONS_FEATURES_WEB_SEARCH=false    # Web search functie?
    - USER_PERMISSIONS_FEATURES_IMAGE_GENERATION=false # AI-afbeeldingen genereren?
    - USER_PERMISSIONS_FEATURES_CODE_INTERPRETER=false # Code interpreter toegang?
    - USER_PERMISSIONS_CHAT_CONTROLS=false          # Extra chatbediening zichtbaar?
    - VERSIMPELAAR=true                             # 'Versimpelaar' (app) activeren

    # 6. Privacy, analytics & tracking 
    - SCARF_NO_ANALYTICS=true                       # Geen externe analytics (Scarf)
    - DO_NOT_TRACK=true                             # 'Niet volgen'-headers instellen
    - ANONYMIZED_TELEMETRY=true                     # Telemetrie volledig anoniem

    # 7. Database / opslag
    - DATABASE_URL=postgresql://<db_gebruiker>:<db_wachtwoord>@<db_host>:<db_poort>/<db_naam> # Database verbinding

    # 8. Documentverwerking
    - CONTENT_EXTRACTION_ENGINE="tika"              # Engine voor documentextractie
    - TIKA_SERVER_URL="http://tika:9998"            # URL van Tika-server

    # 9. Prompts / promptinstellingen
    - TITLE_GENERATION_PROMPT_TEMPLATE=$TITLE_GENERATION_PROMPT_TEMPLATE
    - TAGS_GENERATION_PROMPT_TEMPLATE=$TAGS_GENERATION_PROMPT_TEMPLATE
    - RAG_TEMPLATE=$RAG_TEMPLATE
    - DEFAULT_PROMPT_SUGGESTIONS=$DEFAULT_PROMPT_SUGGESTIONS

    volumes:
      - ./open-webui:/app/backend/data
      - ./static:/app/build/static
    depends_on:
      - litellm
      - db
    extra_hosts:
      - host.docker.internal:host-gateway

  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    restart: always
    ports:
      - 4000:4000
    environment:
      - AZURE_API_KEY=<AZURE_API_KEY>
      - AZURE_API_BASE=https://<azure_openai_endpoint>/
      - AZURE_API_VERSION=2024-05-01-preview
    volumes:
      - ./litellm/litellm_config.yaml:/app/config.yaml
    command: --config /app/config.yaml

  tika:
    image: apache/tika:latest-full
    container_name: tika
    restart: unless-stopped
    ports:
      - "9998:9998"

  db:
    image: postgres:16
    restart: always
    environment:
      POSTGRES_DB=<database_naam>
      POSTGRES_USER=<database_gebruiker>
      POSTGRES_PASSWORD=<database_wachtwoord>
    volumes:
      - openwebui-pgdata:/var/lib/postgresql/data
    ports:
      - "<db_poort>:<db_poort>"

volumes:
  openwebui-pgdata:
```

### 2.2 LiteLLM Configuratie

LiteLLM fungeert als router én adapter tussen de applicatie (zoals OpenWebUI) en verschillende AI-taalmodellen (bijvoorbeeld van Azure OpenAI). Met LiteLLM kun je meerdere leveranciers en modellen naast elkaar beschikbaar stellen, uitgebreide router-logica zoals load balancing toepassen, het gebruik monitoren en limieten instellen (bijvoorbeeld op groep-niveau).

In dit configuratiebestand stel je in:

- Welke taalmodellen gebruikt worden, en waar die draaien (endpoints/regio’s)
- Hoe LiteLLM moet verbinden (API-sleutels, versies)
- (Optioneel) router-logica zoals load balancing en fallback
- (Optioneel) gebruiksmonitoring en limieten per gebruiker of groep

#### **Voorbeeld** `litellm_config.yaml`

```
model_list:
  # West-Europa endpoint
  - model_name: azure-gpt-4o
    litellm_params:
      model: azure/gpt-4o                         # Modelnaam zoals aangemaakt op Azure OpenAI
      api_base: <AZURE_API_BASE_WESTEUROPE>       # Voorbeeld: https://<resource>.openai.azure.com/
      api_key: <AZURE_API_KEY>                    # API key (zet deze altijd in je .env)
      api_version: 2024-05-01-preview             # API-versie voor Azure OpenAI

  # Frankrijk endpoint
  - model_name: azure-gpt-4o
    litellm_params:
      model: azure/gpt-4o
      api_base: <AZURE_API_BASE_FRANCECENTRAL>    # Voorbeeld: https://<resource>.openai.azure.com/
      api_key: <AZURE_API_KEY>
      api_version: 2024-05-01-preview
  
  ...

  # West-Europa embedding-model
  - model_name: azure-text-embedding-3-large
    litellm_params:
      model: azure/text-embedding-3-large
      api_base: <AZURE_API_BASE_WESTEUROPE>       # Zelfde als hierboven, ander deploy-model
      api_key: <AZURE_API_KEY>
      api_version: 2024-05-01-preview

  # Frankrijk embedding-model
  - model_name: azure-text-embedding-3-large
    litellm_params:
      model: azure/text-embedding-3-large
      api_base: <AZURE_API_BASE_FRANCECENTRAL>
      api_key: <AZURE_API_KEY>
      api_version: 2024-05-01-preview

router_settings:
  - routing_strategy: latency-based-routing        # Loadbalancing: automatisch snelste endpoint kiezen
```

## Opmerkingen

- Gebruik áltijd `.env`-bestanden voor geheime waarden en verwijs in config-bestanden naar variabele namen (zoals `${VAR_NAAM}`), niet naar harde waarden.
- Kies leveranciers, endpoints en modellen zorgvuldig met oog op betrouwbaarheid én gegevensbescherming (AVG/Privacy).
- Beperk toegang tot gevoelige functies en beheer gebruikers-/rollen via SSO (bijv. Entra ID).
