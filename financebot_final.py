#!/usr/bin/env python3
"""
🤖 BOT TELEGRAM AVANZATO - Personal Finance AI Assistant
📊 Sistema completo: Spese + Analytics + AI + Grafici
💾 Storage CSV locale - No servizi esterni
"""

import os
import re
import json
import logging
import pandas as pd
import threading
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
from http.server import HTTPServer, BaseHTTPRequestHandler

# Import sistemi locali
from spese_manager import SpeseManager
from analytics import SpeseAnalytics  
from ai_predictor import SpeseAI

# Logging produzione
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('financebot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Environment
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

class FinanceBotAI:
    """Bot AI per gestione finanze personali con OpenAI e ricavi"""
    
    def __init__(self):
        self.spese_manager = SpeseManager()
        self.analytics = SpeseAnalytics()
        self.ai = SpeseAI()
        self.openai_client = openai_client
        
        # Modalità corrente (spese o ricavi)
        self.user_modes = {}  # user_id -> 'spese' | 'ricavi' | None
    
    def parse_transazione(self, testo: str, tipo: str = 'spesa') -> dict:
        """Parse intelligente di transazioni (spese/ricavi) da testo naturale"""
        patterns = [
            r'(€?\s*\d+[.,]?\d*)\s+(.+)',
            r'(.+?)\s+(€?\s*\d+[.,]?\d*)$',
            r'ho\s+(speso|guadagnato|ricevuto)\s+(€?\s*\d+[.,]?\d*)\s+(per|da|di)\s+(.+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, testo.lower().strip())
            if match:
                groups = match.groups()
                
                if len(groups) == 4:  # Pattern con verbo
                    _, importo_str, _, descrizione = groups
                else:  # Pattern semplice
                    p1, p2 = groups
                    for parte in [p1, p2]:
                        clean = parte.replace('€', '').replace(',', '.').strip()
                        if re.match(r'^\d+\.?\d*$', clean):
                            importo_str = clean
                            descrizione = p1 if parte == p2 else p2
                            break
                    else:
                        continue
                
                try:
                    importo = float(importo_str.replace('€', '').replace(',', '.').strip())
                    desc_clean = descrizione.strip()
                    categoria = self._categorize_with_openai(desc_clean, tipo)
                    
                    return {
                        'successo': True,
                        'importo': importo,
                        'descrizione': desc_clean,
                        'categoria': categoria,
                        'tipo': tipo
                    }
                except ValueError:
                    continue
        
        return {'successo': False}
    
    def _categorize_with_openai(self, descrizione: str, tipo: str) -> str:
        """Categorizzazione intelligente con OpenAI GPT"""
        if not self.openai_client:
            return self._fallback_categorize(descrizione, tipo)
        
        try:
            if tipo == 'spesa':
                categorie = "Trasporti, Alimentari, Ristorazione, Casa, Salute, Svago, Abbigliamento, Varie"
                prompt = f"""Categorizza questa spesa in una delle seguenti categorie: {categorie}

Spesa: "{descrizione}"

Regole:
- Trasporti: benzina, carburante, treni, bus, taxi, parcheggi, assicurazione auto
- Alimentari: supermercati, spesa alimentare, pane, latte, frutta, verdura  
- Ristorazione: ristoranti, bar, caffè, pizzerie, takeaway, delivery
- Casa: bollette, affitto, mobili, elettrodomestici, internet, telefono
- Salute: farmacie, visite mediche, medicine, analisi
- Svago: cinema, libri, palestra, sport, giochi, viaggi
- Abbigliamento: vestiti, scarpe, accessori
- Varie: tutto il resto

Rispondi solo con il nome della categoria."""

            else:  # ricavo
                categorie = "Stipendio, Freelance, Famiglia, Investimenti, Vendite, Altri"
                prompt = f"""Categorizza questo ricavo in una delle seguenti categorie: {categorie}

Ricavo: "{descrizione}"

Regole:
- Stipendio: salario, busta paga, lavoro principale
- Freelance: consulenze, lavori secondari, progetti
- Famiglia: paghette, regali nonni, genitori, contributi familiari
- Investimenti: dividendi, interessi, capital gain, rendite
- Vendite: vendita oggetti usati, marketplace, e-commerce
- Altri: qualsiasi altra entrata

Rispondi solo con il nome della categoria."""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1
            )
            
            categoria = response.choices[0].message.content.strip()
            
            # Valida la risposta
            categorie_valide = {
                'spesa': ['Trasporti', 'Alimentari', 'Ristorazione', 'Casa', 'Salute', 'Svago', 'Abbigliamento', 'Varie'],
                'ricavo': ['Stipendio', 'Freelance', 'Famiglia', 'Investimenti', 'Vendite', 'Altri']
            }
            
            if categoria in categorie_valide[tipo]:
                return categoria
            else:
                return 'Varie' if tipo == 'spesa' else 'Altri'
                
        except Exception as e:
            logger.warning(f"Errore OpenAI categorization: {e}")
            return self._fallback_categorize(descrizione, tipo)
    
    def _fallback_categorize(self, descrizione: str, tipo: str) -> str:
        """Categorizzazione fallback senza OpenAI"""
        desc_lower = descrizione.lower()
        
        if tipo == 'spesa':
            categorie_map = {
                'Trasporti': ['benzina', 'treno', 'bus', 'taxi', 'parcheggio', 'auto'],
                'Alimentari': ['supermercato', 'spesa', 'pane', 'latte', 'coop', 'lidl'],
                'Ristorazione': ['ristorante', 'bar', 'caffè', 'pizza', 'pranzo', 'cena'],
                'Casa': ['bolletta', 'affitto', 'luce', 'gas', 'internet', 'casa'],
                'Salute': ['farmacia', 'dottore', 'medico', 'medicina'],
                'Svago': ['cinema', 'libro', 'palestra', 'sport', 'gioco'],
                'Abbigliamento': ['vestiti', 'scarpe', 'maglietta', 'pantaloni']
            }
            
            for categoria, keywords in categorie_map.items():
                if any(kw in desc_lower for kw in keywords):
                    return categoria
            return 'Varie'
        
        else:  # ricavo
            categorie_map = {
                'Stipendio': ['stipendio', 'salario', 'busta', 'paga', 'lavoro'],
                'Freelance': ['consulenza', 'freelance', 'progetto', 'cliente'],
                'Famiglia': ['paghetta', 'nonna', 'nonno', 'mamma', 'papà', 'famiglia'],
                'Investimenti': ['dividendo', 'interesse', 'investimento', 'borsa'],
                'Vendite': ['vendita', 'vendo', 'usato', 'marketplace']
            }
            
            for categoria, keywords in categorie_map.items():
                if any(kw in desc_lower for kw in keywords):
                    return categoria
            return 'Altri'

# Istanza globale
bot = FinanceBotAI()

# HANDLERS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messaggio = """🤖 *Finance AI Bot 2.0 - Con OpenAI!*

� *Gestione Spese e Ricavi:*
• `/segnaspese` - Modalità registrazione spese
• `/segnaricavi` - Modalità registrazione entrate  
• `/modalinormale` - Torna alla modalità normale

📊 *Analytics Avanzate:*
• `/grafici` - Visualizzazioni complete
• `/budget` - Stato budget vs spese
• `/bilancio` - Entrate vs Uscite  
• `/stats` - Statistiche generali

🤖 *AI Features (OpenAI):*
• Categorizzazione intelligente automatica
• `/predizioni` - Prevede spese future
• `/pattern` - Analizza comportamenti
• `/raccomandazioni` - Consigli personalizzati

📚 `/help` per guida completa

🚀 **Novità**: Ora gestisco anche i tuoi ricavi!"""
    
    await update.message.reply_text(messaggio, parse_mode='Markdown')

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messaggio = """📚 *Guida Finance AI Bot*

💡 *Esempi di spese:*
• `15.50 benzina`
• `€25 spesa supermercato`  
• `ho speso 12 per pranzo`
• `cinema 8.50`

🎯 *Categorizzazione automatica:*
• 🚗 Trasporti, 🛒 Alimentari, 🍽️ Ristorazione
• 🏠 Casa, ⚕️ Salute, 🎭 Svago, 👕 Abbigliamento

📊 *Analytics disponibili:*
• Grafici trend, budget vs reale, categorie
• Statistiche complete e pattern comportamentali  
• Predizioni AI basate su cronologia

⚙️ *Configurazione:*
Modifica `config.json` per budget personalizzati

💾 *Dati:* Tutto salvato localmente in CSV"""
    
    await update.message.reply_text(messaggio, parse_mode='Markdown')

async def segnaspese(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Attiva modalità registrazione spese"""
    logger.info(f"🔥 /segnaspese chiamato da user {update.effective_user.id}")
    user_id = update.effective_user.id
    bot.user_modes[user_id] = 'spese'
    logger.info(f"✅ Modalità spese attivata per user {user_id}")
    
    messaggio = """💸 *MODALITÀ SPESE ATTIVATA*

Ora tutti i tuoi messaggi saranno interpretati come spese.

📝 *Come registrare:*
• `15.50 benzina`
• `25 spesa supermercato`  
• `ho speso 12€ per pranzo`

🤖 *Categorizzazione automatica con OpenAI*
Le tue spese verranno categorizzate intelligentemente.

🔄 *Cambia modalità:*
• `/segnaricavi` - Per registrare entrate
• `/modalinormale` - Per tornare alla modalità normale"""
    
    await update.message.reply_text(messaggio, parse_mode='Markdown')

async def segnaricavi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Attiva modalità registrazione ricavi/entrate"""
    user_id = update.effective_user.id
    bot.user_modes[user_id] = 'ricavi'
    
    messaggio = """💰 *MODALITÀ RICAVI ATTIVATA*

Ora tutti i tuoi messaggi saranno interpretati come entrate/ricavi.

📝 *Come registrare:*
• `1500 stipendio dicembre`
• `200 freelance progetto web`  
• `50 vendita oggetto usato`
• `100 regalo famiglia`

🤖 *Categorizzazione automatica con OpenAI*
Le tue entrate verranno categorizzate intelligentemente.

💡 *Categorie ricavi:*
• Stipendio, Freelance, Famiglia
• Investimenti, Vendite, Altri

🔄 *Cambia modalità:*
• `/segnaspese` - Per registrare spese
• `/modalinormale` - Per tornare alla modalità normale"""
    
    await update.message.reply_text(messaggio, parse_mode='Markdown')

async def modalinormale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Torna alla modalità normale (senza auto-interpretazione)"""
    user_id = update.effective_user.id
    bot.user_modes[user_id] = None
    
    messaggio = """🔄 *MODALITÀ NORMALE ATTIVATA*

Modalità automatica disattivata. 

📝 *Per registrare:*
• Usa `/segnaspese` per attivare modalità spese
• Usa `/segnaricavi` per attivare modalità ricavi  
• Oppure usa i comandi specifici come sempre

💡 *Tip:* Le modalità specifiche rendono più veloce la registrazione!"""
    
    await update.message.reply_text(messaggio, parse_mode='Markdown')

async def bilancio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra bilancio entrate vs uscite"""
    await update.message.reply_text("💰 Calcolo bilancio...")
    
    try:
        df = bot.spese_manager.get_dataframe()
        
        if df.empty:
            await update.message.reply_text("❌ Nessun dato disponibile")
            return
        
        # Filtra per mese corrente
        df['data'] = pd.to_datetime(df['data'])
        mese_corrente = df[df['data'].dt.month == datetime.now().month]
        
        spese_totali = mese_corrente[mese_corrente['tipo'] == 'spesa']['importo'].sum()
        ricavi_totali = mese_corrente[mese_corrente['tipo'] == 'ricavo']['importo'].sum()
        bilancio_netto = ricavi_totali - spese_totali
        
        # Emoji per bilancio
        emoji_bilancio = "📈" if bilancio_netto > 0 else "📉" if bilancio_netto < 0 else "⚖️"
        
        messaggio = f"""💰 *BILANCIO MENSILE*

📈 *Entrate:* €{ricavi_totali:.2f}
📉 *Uscite:* €{spese_totali:.2f}
{emoji_bilancio} *Bilancio:* €{bilancio_netto:.2f}

📊 *Dettagli:*
• Transazioni totali: {len(mese_corrente)}
• Media giornaliera spese: €{spese_totali/30:.2f}
• % Risparmiato: {(bilancio_netto/ricavi_totali*100):.1f}%" if ricavi_totali > 0 else "N/A"
"""
        
        await update.message.reply_text(messaggio, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Errore calcolo bilancio: {e}")

async def grafici(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Generazione grafici...")
    
    try:
        grafici_paths = bot.analytics.genera_report_completo()
        
        if not grafici_paths:
            await update.message.reply_text("❌ Nessun dato per grafici")
            return
        
        titoli = {
            'torta': '🥧 Spese per Categoria',
            'trend': '📈 Trend Mensile',
            'budget': '💰 Budget vs Reale', 
            'settimana': '📅 Pattern Settimanali'
        }
        
        for nome, path in grafici_paths.items():
            if path and os.path.exists(path):
                with open(path, 'rb') as f:
                    caption = titoli.get(nome, 'Grafico')
                    await update.message.reply_photo(photo=f, caption=caption)
        
        await update.message.reply_text("✅ Grafici completati!")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Errore: {e}")

async def budget_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        budget_info = bot.spese_manager.verifica_budget()
        
        messaggio = f"""💰 *Budget Status - {budget_info['mese']}*

📊 *Totali:*
• Budget: €{budget_info['totale_budget']:.2f}
• Speso: €{budget_info['totale_spese']:.2f}  
• Rimanente: €{budget_info['totale_budget'] - budget_info['totale_spese']:.2f}

📂 *Per Categoria:*
"""
        
        for cat, info in budget_info['categorie'].items():
            perc = info['percentuale']
            emoji = '🔴' if perc >= 90 else '🟡' if perc >= 75 else '🟢'
            messaggio += f"{emoji} {cat}: €{info['speso']:.0f}/€{info['budget']} ({perc:.0f}%)\n"
        
        if budget_info['alert']:
            messaggio += "\n⚠️ *Alert:*\n"
            for alert in budget_info['alert']:
                messaggio += f"• {alert}\n"
        
        await update.message.reply_text(messaggio, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Errore: {e}")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        stats = bot.spese_manager.get_statistiche_generali()
        
        messaggio = f"""📊 *Statistiche Generali*

📈 *Overview:*
• Records: {stats.get('totale_records', 0)}
• Periodo: {stats.get('periodo', {}).get('da', 'N/A')} → {stats.get('periodo', {}).get('a', 'N/A')}
• Totale speso: €{stats.get('spesa_totale', 0):.2f}
• Media per spesa: €{stats.get('spesa_media', 0):.2f}

🏆 *Record:*
• Top categoria: {stats.get('categoria_piu_costosa', 'N/A')}  
• Mese più costoso: {stats.get('mese_piu_costoso', 'N/A')}
"""
        
        await update.message.reply_text(messaggio, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Errore stats: {e}")

async def predizioni_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 AI Training e predizioni...")
    
    try:
        # Training
        training = bot.ai.train_modello_spesa_totale()
        
        if 'errore' in training:
            await update.message.reply_text(f"⚠️ {training['errore']}")
            return
        
        # Predizione
        pred = bot.ai.predici_spesa_mese_prossimo()
        
        if 'errore' in pred:
            await update.message.reply_text(f"❌ {pred['errore']}")
            return
        
        messaggio = f"""🔮 *AI Predictions - {pred['mese']}*

💰 *Spesa Prevista:* €{pred['predizione']:.2f}

📊 *Range Confidenza:*
• Min: €{pred['range_min']:.2f}
• Max: €{pred['range_max']:.2f}  
• Affidabilità: {pred['confidence']}

🧠 *Modello:*
• R²: {training.get('r2', 'N/A')}
• Samples: {training['samples_train']}
        """
        
        await update.message.reply_text(messaggio, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Errore AI: {e}")

async def pattern_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pattern = bot.ai.analizza_pattern_spesa()
        
        if 'errore' in pattern:
            await update.message.reply_text(f"❌ {pattern['errore']}")
            return
        
        messaggio = f"""🔍 *Pattern Analysis*

📅 *Giorno più costoso:* {pattern.get('giorno_piu_costoso', 'N/A')}

📊 *Stats:*
• Top categoria: {pattern.get('categoria_piu_costosa', 'N/A')}
• Spesa media/mese: €{pattern.get('spesa_media_mensile', 0):.2f}
• Volatilità: €{pattern.get('volatilita', 0):.2f}

📈 *Trend:* {pattern.get('trend_direzione', 'Stabile')}
        """
        
        await update.message.reply_text(messaggio, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Errore pattern: {e}")

async def raccomandazioni_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        racc = bot.ai.raccomandazioni_budget()
        
        messaggio = "💡 *AI Recommendations:*\n\n"
        for i, r in enumerate(racc, 1):
            messaggio += f"{i}. {r}\n\n"
        
        await update.message.reply_text(messaggio, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Errore: {e}")

async def gestisci_testo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler principale per transazioni (spese/ricavi)"""
    testo = update.message.text
    user = update.effective_user.first_name or "User"
    user_id = update.effective_user.id
    
    logger.info(f"📨 {user}: {testo}")
    
    # Controlla modalità utente
    modalita = bot.user_modes.get(user_id, None)
    
    if modalita is None:
        # Modalità normale - non interpreta automaticamente
        await update.message.reply_text(
            "💡 Usa `/segnaspese` o `/segnaricavi` per attivare la modalità automatica, "
            "oppure specifica meglio il comando."
        )
        return
    
    # Determina tipo di transazione
    tipo = modalita  # 'spese' o 'ricavi'
    
    # Parse transazione con OpenAI
    transazione = bot.parse_transazione(testo, tipo)
    
    if transazione['successo']:
        # Salva nel database con tipo corretto
        success = bot.spese_manager.aggiungi_transazione(
            nome_transazione=transazione['descrizione'],
            categoria=transazione['categoria'],
            importo=transazione['importo'],
            tipo='spesa' if tipo == 'spese' else 'ricavo',
            note=f"Bot - {user}"
        )
        
        if success:
            # Emoji per categorie
            emoji_spese = {
                'Trasporti': '🚗', 'Alimentari': '🛒', 'Ristorazione': '🍽️',
                'Casa': '🏠', 'Salute': '⚕️', 'Svago': '🎭', 
                'Abbigliamento': '👕', 'Varie': '📝'
            }
            
            emoji_ricavi = {
                'Stipendio': '💼', 'Freelance': '💻', 'Famiglia': '👨‍👩‍👧‍👦',
                'Investimenti': '📈', 'Vendite': '🛍️', 'Altri': '💰'
            }
            
            emoji_dict = emoji_ricavi if tipo == 'ricavi' else emoji_spese
            emoji = emoji_dict.get(transazione['categoria'], '📝')
            
            tipo_display = "Ricavo" if tipo == 'ricavi' else "Spesa"
            
            messaggio = f"""✅ *{tipo_display} Salvat{'o' if tipo == 'ricavi' else 'a'}!*

💰 **€{transazione['importo']:.2f}**
📝 {transazione['descrizione']}  
{emoji} {transazione['categoria']}
📅 {datetime.now().strftime("%d/%m/%Y")}
🤖 Categorizzato con OpenAI

💾 Database aggiornato"""
            
            await update.message.reply_text(messaggio, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Errore salvataggio")
    
    else:
        tipo_esempi = "ricavi" if tipo == 'ricavi' else "spese"
        esempi = {
            'spese': ["15.50 benzina", "€25 supermercato", "12 pranzo"],
            'ricavi': ["1500 stipendio", "€200 freelance", "50 vendita"]
        }
        
        messaggio = f"""❌ *Formato non riconosciuto*

💡 *Esempi per {tipo_esempi}:*
"""
        for esempio in esempi[tipo_esempi]:
            messaggio += f"• `{esempio}`\n"
        
        await update.message.reply_text(messaggio, parse_mode='Markdown')

async def credito_openai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔍 Mostra info credito e usage OpenAI"""
    logger.info(f"🔍 /credito chiamato da {update.effective_user.id}")
    
    await update.message.reply_text("🔍 Controllo credito OpenAI...", parse_mode='HTML')
    
    try:
        # Controlla credito
        credito_info = bot.spese_manager.check_openai_credit()
        
        if "error" in credito_info:
            await update.message.reply_text(
                f"❌ <b>Errore controllo credito:</b>\n{credito_info['error']}", 
                parse_mode='HTML'
            )
            return
        
        # Ottieni stima costi
        stima_costi = bot.spese_manager.stima_costo_mensile()
        
        # Ottieni stima costi
        stima_costi = bot.spese_manager.stima_costo_mensile()
        
        # Prepara messaggio basato sullo status
        status = credito_info.get('status', 'unknown')
        
        if status == "success":
            # Dati reali dall'API
            messaggio = f"""💳 <b>OPENAI USAGE - DATI REALI</b>

✅ <b>Status API:</b>
🔸 Connessione: ✅ Funzionante
🔸 Periodo: {credito_info.get('periodo_attuale', 'N/A')}
🔸 Giorni con dati: {credito_info.get('giorni_con_dati', 0)}

📊 <b>Usage Effettivo:</b>
🔸 Richieste totali: {credito_info.get('richieste_totali', 0):,}
🔸 Token input: {credito_info.get('token_input', 0):,}
🔸 Token output: {credito_info.get('token_output', 0):,}
🔸 Token totali: {credito_info.get('token_totali', 0):,}

💰 <b>Costi Reali:</b>
🔸 Costo mese: {credito_info.get('costo_eur', '€0.00')}
🔸 Usage totale: {credito_info.get('usage_totale', 0)}

📈 <b>Stima Mensile:</b>
🔸 Richieste/giorno: {stima_costi['richieste_giornaliere']}
🔸 Proiezione fine mese: {stima_costi['costo_mensile_eur']}

📊 <b>Dashboard:</b>
🔗 <a href="{credito_info.get('dashboard_url')}">OpenAI Usage Dashboard</a>

⏰ <b>Aggiornamento:</b> {credito_info.get('ultimo_controllo', 'N/A')}
"""
        
        elif status == "limited_access":
            # API funziona ma senza accesso usage
            messaggio = f"""💳 <b>OPENAI STATUS</b>

✅ <b>API Status:</b>
🔸 Connessione: ✅ Attiva
🔸 Modelli disponibili: {credito_info.get('modelli_disponibili', 'N/A')}
🔸 Accesso Usage: ❌ Non disponibile

📈 <b>Stima Costi (Proiezione):</b>
🔸 Richieste/giorno: {stima_costi['richieste_giornaliere']}
🔸 Costo mensile stimato: {stima_costi['costo_mensile_eur']}
🔸 Token stimati: {stima_costi['token_stimati_mese']:,}

📊 <b>Monitoraggio Manuale:</b>
🔗 <a href="{credito_info.get('dashboard_url')}">Dashboard OpenAI Usage</a>

💡 <b>Nota:</b> {credito_info.get('note', 'Verifica manualmente su dashboard')}

⏰ <b>Controllo:</b> {credito_info.get('ultimo_controllo', 'N/A')}
"""
        
        else:
            # Errore o fallback
            messaggio = f"""� <b>OPENAI STATUS - LIMITATO</b>

⚠️ <b>Status:</b>
🔸 API Key: {'✅' if credito_info.get('api_key_valida') else '❌'} 
🔸 Periodo: {credito_info.get('periodo_attuale', 'N/A')}

📈 <b>Stima Teorica:</b>
🔸 Richieste/giorno: {stima_costi['richieste_giornaliere']}
🔸 Costo mensile: {stima_costi['costo_mensile_eur']}

📊 <b>Verifica Manuale:</b>
🔗 <a href="{credito_info.get('dashboard_url')}">Dashboard OpenAI</a>

💡 <b>Nota:</b> {credito_info.get('note', 'Controlla dashboard per dettagli')}

⏰ <b>Ultimo tentativo:</b> {credito_info.get('ultimo_controllo', 'N/A')}
"""
        
        await update.message.reply_text(messaggio, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"❌ Errore comando credito: {e}")
        await update.message.reply_text(
            f"❌ Errore interno: {str(e)}", 
            parse_mode='HTML'
        )

async def setup_bot_commands(app):
    """Configura il menu dei comandi del bot"""
    commands = [
        BotCommand("start", "🚀 Avvia il bot e mostra menu principale"),
        BotCommand("help", "📚 Guida completa all'uso del bot"),
        BotCommand("segnaspese", "💸 Attiva modalità registrazione spese"),
        BotCommand("segnaricavi", "💰 Attiva modalità registrazione ricavi"),
        BotCommand("modalinormale", "🔄 Torna alla modalità normale"),
        BotCommand("bilancio", "⚖️ Mostra bilancio entrate vs uscite"),
        BotCommand("grafici", "📊 Genera grafici e visualizzazioni"),
        BotCommand("budget", "💰 Verifica status budget mensile"),
        BotCommand("stats", "📈 Statistiche complete del periodo"),
        BotCommand("predizioni", "🔮 Predizioni AI spese future"),
        BotCommand("pattern", "🔍 Analisi pattern comportamentali"),
        BotCommand("credito", "💳 Controlla credito e usage OpenAI"),
        BotCommand("raccomandazioni", "💡 Consigli AI personalizzati")
    ]
    
    await app.bot.set_my_commands(commands)
    logger.info("✅ Menu comandi bot configurato!")

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Semplice health check per Render"""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is running!')
    
    def log_message(self, format, *args):
        # Disable HTTP server logging
        pass

def start_health_server():
    """Avvia server HTTP per health check su Render"""
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"✅ Health server avviato su porta {port}")
    server.serve_forever()

def main():
    """Avvia il Finance AI Bot"""
    print("=" * 50)
    print("🤖 FINANCE AI BOT")  
    print("📊 Analytics + AI + Grafici")
    print("💾 Storage CSV Locale")
    print("=" * 50)
    
    if not TOKEN:
        print("❌ Token mancante!")
        return
    
    # Avvia health server in background per Render
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Setup bot
    app = Application.builder().token(TOKEN).build()
    
    # Comandi
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("segnaspese", segnaspese))
    app.add_handler(CommandHandler("segnaricavi", segnaricavi))
    app.add_handler(CommandHandler("modalinormale", modalinormale))
    app.add_handler(CommandHandler("bilancio", bilancio))
    app.add_handler(CommandHandler("grafici", grafici))
    app.add_handler(CommandHandler("budget", budget_cmd))  
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("predizioni", predizioni_cmd))
    app.add_handler(CommandHandler("pattern", pattern_cmd))
    app.add_handler(CommandHandler("raccomandazioni", raccomandazioni_cmd))
    app.add_handler(CommandHandler("credito", credito_openai))
    
    # Testi (spese)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gestisci_testo))
    
    print("✅ Bot configurato!")
    print("📱 @SpesaAIbot")
    print("🚀 AVVIATO - Ctrl+C per fermare")
    print("=" * 50)
    
    try:
        # Avvia il bot e configura comandi
        async def post_init(app):
            await setup_bot_commands(app)
        
        app.post_init = post_init
        app.run_polling()
    except KeyboardInterrupt:
        print("\n🔴 Bot fermato")

if __name__ == '__main__':
    main()