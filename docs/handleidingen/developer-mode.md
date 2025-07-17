# GovChat-NL
Welkom bij de **GovChat-NL Ontwikkel Handleiding**!  
In deze handleiding leggen we stap voor stap uit hoe je een ontwikkelomgeving opzet voor GovChat-NL.

---

## 📥 Initiele Installatie

### **0. Visual Studio Code**
- Installeer en gebruik **Visual Studio Code (VS Code)** om de code te bewerken.


---

### **1. Installatie van WSL (Windows Subsystem for Linux)**  
1. Open **PowerShell** binnen VS-Code.  
2. Voer het volgende commando uit om **WSL** te installeren, **WSL** gebruiken we om de ontwikkelomgeving te runnen:

    ```bash
    wsl --install
    ```

3. Herstart je computer om **WSL** te activeren.
4. Controleer of **WSL** correct geïnstalleerd is:

    ```bash
    wsl --list --verbose
    ```

   Dit toont een lijst van geïnstalleerde distributies en hun versie. Zorg ervoor dat **WSL** is ingesteld.

---

### **2. Configuratie van de Linux-omgeving**  
1. Start je WSL-distributie via PowerShell in VS Code:

    ```bash
    wsl
    ```

2. Werk de pakketlijst bij en installeer updates:

    ```bash
    sudo apt update && sudo apt upgrade -y
    ```

---

### **3. Installatie van Conda**  
**Miniconda** is aanbevolen vanwege de compactere installatie.  
1. Download het installatiebestand binnen de **WSL-terminal** in VS-Code:

    ```bash
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    ```

2. Voer het installatiebestand uit en volg de instructies. Vergeet niet de licentie te accepteren en de standaardpaden in te stellen.  
3. Herstart de shell:

    ```bash
    source ~/.bashrc
    ```

4. Controleer of **Conda** correct is geïnstalleerd:

    ```bash
    conda --version
    ```

---

### **4. 2x WSL openen in VS Code**
1. Open twee WSL-terminals in VS Code:
   ![WSL-Terminals](images/WSL-shell.png)
2. Als het project niet zichtbaar is, start Poweshell normaal op en typ:

    ```bash
    wsl
    ```

3. Clone vervolgens het **GovChat-NL** project:

    ```bash
    git clone https://github.com/jeannotdamoiseaux/GovChat-NL.git
    cd GovChat-NL
    ```

---

### **5. Frontend Setup (eerste terminal)**  
1. Maak een **.env** bestand aan door het voorbeeldbestand te kopiëren:

    ```bash
    cp -RPp .env.example .env
    ```

2. Open het gegenereerde **.env** bestand en pas de gewenste keys aan.  
3. Installeer dependencies:

    ```bash
    npm install
    ```

4. Start de frontend:

    ```bash
    npm run dev
    ```

---

### **6. Backend Setup (tweede terminal)**  
1. Navigeer naar de backend-folder:

    ```bash
    cd GovChat-NL/backend
    ```

2. Maak een virtuele Conda-omgeving aan:

    ```bash
    conda create --name GovChat-NL python=3.11
    ```

3. Activeer de Conda-omgeving:

    ```bash
    conda activate GovChat-NL
    ```

4. Installeer backend-pakketten:

    ```bash
    pip install -r requirements.txt -U
    ```

5. Start de backend:

    ```bash
    sh dev.sh
    ```

---

### **7. Admin inlog (Voorbeeld)**  
- **Gebruikersnaam:** `root`  
- **E-mail:** `root@toor.nl`  
- **Wachtwoord:** `toor`  

---
##  🔄Opnieuw opstarten 
 
 Herhaal stap **2 en 3** specifiek de volgende commandos daarbinnen: 
- **Eerste Terminal** 
```bash
    npm run dev
``` 
- **Tweede Terminal**
```bash
    cd GovChat-NL/backend
```
```bash
    conda activate GovChat-NL
```
```bash
    sh dev.sh
``` 

---

## ⚙️ Troubleshooting

### **Error Backend Required**
| Error | Beschrijving                                                                                     |
|-------|-------------------------------------------------------------------------------------------------|
| ![Backend Required](images/backend-required.png) | Dit geeft aan dat "CORS_ALLOW_ORIGIN" niet lokaal is ingesteld. Pas dit aan naar "localhost". |

---

## 🤖 Lite LLM API Connectie

### **1. Docker installeren**
Download en installeer **Docker** via:  
[Officiële Docker Download](https://www.docker.com/)

### **2. Configureer credentials**
Update de volgende bestanden waar nodig:  
- **.env**  
- **litellm/litellm_config.yaml**

### **3. Run Docker-services**
- Klik op **"Run all services"** in het bestand `docker-compose-lite-llm-local.yaml` binnen VS Code.  
- Als de image binnen Docker al eerder is gebruikt, start de image opnieuw binnen de Docker-app.