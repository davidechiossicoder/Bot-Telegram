# 🐍 GUIDA COMPLETA: Deploy su PythonAnywhere

## 🆓 **PYTHONANYWHERE - Hosting Gratuito per Bot Telegram**

PythonAnywhere offre hosting Python gratuito perfetto per bot Telegram 24/7!

---

## 📋 **STEP 1: Registrazione PythonAnywhere**

### 1.1 Crea Account Gratuito:

1. Vai su **[pythonanywhere.com](https://pythonanywhere.com)**
2. Clicca **"Pricing & signup"**
3. Seleziona **"Create a Beginner account"** (GRATUITO)
4. Inserisci:
   - **Username:** `davidechiossi` (o quello che preferisci)
   - **Email:** La tua email
   - **Password:** Una password sicura
5. **Verifica email** e attiva l'account

### 1.2 Limiti Account Gratuito:
- ✅ **Always-On Tasks:** 1 (perfetto per 1 bot)
- ✅ **CPU Seconds:** 100/giorno (sufficiente per bot)
- ✅ **Disk Space:** 512MB
- ✅ **Internet access:** Sì (necessario per Telegram API)

---

## 🔧 **STEP 2: Setup Ambiente**

### 2.1 Accedi alla Dashboard:

1. Login su PythonAnywhere
2. Vai su **"Dashboard"**
3. Clicca **"$ Bash console"** per aprire terminale

### 2.2 Clona il Repository:

Nel terminale PythonAnywhere:

```bash
# Clona il tuo repository GitHub
git clone https://github.com/DavideChiossi/finance-ai-bot.git

# Entra nella cartella
cd finance-ai-bot

# Verifica file
ls -la
```

### 2.3 Crea Virtual Environment:

```bash
# Crea ambiente virtuale
python3.10 -m venv botenv

# Attiva l'ambiente
source botenv/bin/activate

# Aggiorna pip
pip install --upgrade pip
```

---

## 📦 **STEP 3: Installazione Dipendenze**

### 3.1 Installa Requirements:

```bash
# Assicurati di essere in /home/davidechiossi/finance-ai-bot/
cd /home/davidechiossi/finance-ai-bot/

# Installa tutte le dipendenze
pip install -r requirements.txt
```

### 3.2 Verifica Installazione:

```bash
# Test import principali
python3 -c "import telegram; print('✅ python-telegram-bot OK')"
python3 -c "import openai; print('✅ OpenAI OK')"
python3 -c "import pandas; print('✅ Pandas OK')"
python3 -c "import matplotlib; print('✅ Matplotlib OK')"
```

---

## 🔑 **STEP 4: Configurazione Variabili Ambiente**

### 4.1 Crea File .env:

```bash
# Vai nella cartella del bot
cd /home/davidechiossi/finance-ai-bot/

# Crea file .env
nano .env
```

### 4.2 Inserisci le Variabili:

Nel file `.env` scrivi:

```env
TELEGRAM_TOKEN=7713482855:AAF4t80yB0eqfQ077EMtNFBf_WNxJJ00VVA
OPENAI_API_KEY=sk-proj-ML5g2jlLDrqJgB3ck7BX0UZWnaGdIYbni3io6ZfmUrCn5XSL2lzdqnCOV2h0sbX8JkmLF3bo2T3BlbkFJ2C5EpuR1r2o_GuSiGaP4exoubNp23pomVCZvy2ak41MjNkZG5HvHVTE5hOOHBLNtLlvCO880kA
```

Salva con: `Ctrl+X` → `Y` → `Enter`

### 4.3 Test Configurazione:

```bash
# Test le variabili
source .env
echo "Token: ${TELEGRAM_TOKEN:0:10}..."
echo "OpenAI: ${OPENAI_API_KEY:0:10}..."
```

---

## 🚀 **STEP 5: Configurazione Always-On Task**

### 5.1 Modifica il Bot per PythonAnywhere:

Prima modifichiamo leggermente il bot per caricare il file `.env`:

```bash
# Modifica il file principale
nano financebot_final.py
```

**Aggiungi all'inizio (dopo gli import):**

```python
# Carica variabili da .env
from dotenv import load_dotenv
load_dotenv()  # ← Aggiungi questa linea
```

### 5.2 Crea Always-On Task:

1. **Dashboard PythonAnywhere** → **"Tasks"**
2. Clicca **"Create an always-on task"**
3. **Command:** 
   ```bash
   /home/davidechiossi/finance-ai-bot/botenv/bin/python /home/davidechiossi/finance-ai-bot/financebot_final.py
   ```
4. **Description:** `Finance AI Bot - Telegram`
5. Clicca **"Create"**

### 5.3 Avvia il Task:

1. Nella lista task, clicca **"Run"**
2. Status diventa **"Running"** 🟢
3. Clicca **"Log"** per vedere output

---

## ✅ **STEP 6: Verifica Funzionamento**

### 6.1 Controlla Log Task:

Nei log dovresti vedere:

```
🤖 FINANCE AI BOT
✅ Bot configurato!
📱 @SpesaAIbot
🚀 AVVIATO - Ctrl+C per fermare
```

### 6.2 Test su Telegram:

1. Apri **@SpesaAIbot**
2. **`/start`** → Dovrebbe rispondere
3. **`/segnaspese`** → Modalità spese attiva
4. **`Colazione 5€`** → Registra spesa con OpenAI

### 6.3 Se Funziona:

```
✅ Bot online 24/7 gratis
✅ Always-On Task attivo
✅ OpenAI categorizzazione
✅ Database CSV persistente
```

---

## 🔧 **STEP 7: Gestione e Maintenance**

### 7.1 Aggiornamenti Futuri:

```bash
# Accedi via SSH
ssh davidechiossi@ssh.pythonanywhere.com

# Aggiorna codice
cd finance-ai-bot
git pull origin main

# Riavvia task dalla Dashboard
```

### 7.2 Monitoring:

- **Dashboard** → **Tasks** → **Log** per vedere output
- CPU usage nel **Dashboard**
- **Files** per gestire file CSV

### 7.3 Backup Database:

```bash
# Download CSV dal dashboard
# Files → finance-ai-bot → spese.csv → Download
```

---

## 💰 **LIMITI GRATUITI PYTHONANYWHERE:**

- ✅ **1 Always-On Task** (sufficiente per il bot)
- ✅ **100 CPU seconds/giorno** (bot Telegram consuma poco)
- ✅ **512MB disk** (più che sufficiente)
- ✅ **Internet access** per API Telegram/OpenAI
- ✅ **Uptime 24/7** garantito

---

## 📞 **Troubleshooting:**

### Se il bot non parte:

1. **Task Log** → Controlla errori
2. **Console** → Test manuale: `python financebot_final.py`
3. **Files** → Verifica `.env` esiste
4. **Requirements** → Reinstalla: `pip install -r requirements.txt`

### Se perde connessione:

- Always-On Task si riavvia automaticamente
- Controlla CPU usage nel dashboard

---

## 🎉 **CONGRATULAZIONI!**

Il tuo **Finance AI Bot** è ora su PythonAnywhere!

🐍 **Hosting Python gratuito**
🤖 **Bot attivo 24/7**
💰 **Nessun costo**
🚀 **Scalabile e affidabile**

**Bot Telegram:** `@SpesaAIbot` - Pronto all'uso! 🎊