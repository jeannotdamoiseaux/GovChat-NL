# GovChat-NL Multi-Tenant Wijzigingen

Dit document beschrijft alle wijzigingen om GovChat-NL generiek te maken voor provincies en gemeentes.

## Draaien van de applicatie

**Vereisten:**
- Node.js versie 18-22 (NIET v24+)
- Python 3.11+

```bash
# Controleer Node versie
node --version  # moet <=22.x.x zijn

# Frontend installeren en starten
npm install --legacy-peer-deps
npm run dev

# Backend starten (in aparte terminal)
cd backend
pip install -r requirements.txt
./dev.sh  # of: uvicorn open_webui.main:app --port 8080 --reload
```

**Admin panel bereiken:**
- Start de app en ga naar `/admin/settings/govchat-nl`
- Alleen toegankelijk voor gebruikers met admin rol

---

## Nieuwe Bestanden

| Bestand | Beschrijving |
|---------|--------------|
| `src/lib/components/admin/Settings/GovChatNL.svelte` | Admin component voor GovChat-NL instellingen |
| `src/routes/(app)/admin/settings/govchat-nl/+page.svelte` | Route voor admin pagina |

## Gewijzigde Bestanden

### Backend (Python)

| Bestand | Wijziging |
|---------|-----------|
| `backend/open_webui/config.py` | Twee nieuwe PersistentConfig variabelen toegevoegd |
| `backend/open_webui/main.py` | Nieuwe imports + config values in `/api/config` response |
| `backend/open_webui/routers/configs.py` | API endpoints `GET/POST /configs/govchat-nl` |

### Frontend (Svelte/TypeScript)

| Bestand | Wijziging |
|---------|-----------|
| `src/lib/components/admin/Settings.svelte` | Import, tab en render conditie voor GovChatNL |
| `src/lib/apis/configs/index.ts` | API functies `getGovChatNLConfig` en `setGovChatNLConfig` |
| `src/lib/components/layout/Help/HelpContent.ts` | `sections` hernoemd naar `defaultSections` + alias |
| `src/lib/components/layout/Help.svelte` | Merge logica voor custom + hidden sections |
| `src/lib/stores/index.ts` | `CustomizationGovChatNL` interface toegevoegd |

---

## Functionaliteit

### Admin Panel (`/admin/settings/govchat-nl`)

**Versimpelaar - B1 Woorden:**
- Woorden toevoegen/verwijderen die behouden blijven bij versimpelen
- Worden opgeslagen in database, niet meer hardcoded

**Handleiding - Standaard Secties:**
- Per sectie zichtbaar/verborgen maken
- Verborgen secties worden niet getoond aan gebruikers

**Handleiding - Eigen Secties:**
- Nieuwe secties toevoegen met:
  - Emoji
  - Titel
  - Inhoud (HTML met opmaak)
  - Positie: voor of na standaard secties

---

## Technische Details

### Nieuwe Config Variabelen (config.py)

```python
HELP_HIDDEN_DEFAULT_SECTIONS = PersistentConfig(
    "HELP_HIDDEN_DEFAULT_SECTIONS",
    "customization.help_hidden_default_sections",
    os.getenv("HELP_HIDDEN_DEFAULT_SECTIONS", "[]")
)

HELP_CUSTOM_SECTIONS = PersistentConfig(
    "HELP_CUSTOM_SECTIONS",
    "customization.help_custom_sections",
    os.getenv("HELP_CUSTOM_SECTIONS", "[]")
)
```

### API Endpoints (configs.py)

```
GET  /api/configs/govchat-nl  - Ophalen configuratie
POST /api/configs/govchat-nl  - Opslaan configuratie
```

### Data Structuur Custom Sectie

```typescript
{
  id: string;           // uniek ID (auto-generated)
  emoji: string;        // bijv. "🏛️"
  title: string;        // bijv. "Over Gemeente X"
  content: string;      // HTML content
  position: 'before' | 'after';  // voor of na standaard
  order: number;        // volgorde
}
```

---

## Geen Wijzigingen aan OpenWebUI Core

Alle wijzigingen blijven binnen GovChat-NL specifieke secties:
- `config.py` - Alleen in "Personalisatie GovChat-NL" sectie
- `main.py` - Alleen in "customization" object
- Nieuwe admin tab is een toevoeging, geen wijziging aan bestaande tabs
