#!/usr/bin/env python3
"""
📊 Sistema Gestione Spese e Analytics 
🔧 Gestione CSV, Budget, Predizioni AI
"""

import pandas as pd
import json
import os
from datetime import datetime, timedelta
import shutil
from typing import Dict, List, Optional, Tuple
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpeseManager:
    """Gestore principale per spese e budget"""
    
    def __init__(self, 
                 csv_file: str = "spese.csv",
                 config_file: str = "config.json",
                 backup_dir: str = "backup"):
        
        self.csv_file = csv_file
        self.config_file = config_file
        self.backup_dir = backup_dir
        
        # Crea directory backup se non esiste
        os.makedirs(backup_dir, exist_ok=True)
        
        # OpenAI API key per monitoraggio
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Inizializza file se non esistono
        self._init_files()
        
        # Carica configurazione
        self.config = self._load_config()
        
    def _init_files(self):
        """Inizializza file CSV e config se non esistono"""
        if not os.path.exists(self.csv_file):
            # Crea CSV con header
            df = pd.DataFrame(columns=['data', 'nome_spesa', 'categoria', 'importo', 'note'])
            df.to_csv(self.csv_file, index=False)
            logger.info(f"✅ Creato {self.csv_file}")
        
        if not os.path.exists(self.config_file):
            # Crea config default
            default_config = {
                "budget_mensile": {
                    "Trasporti": 200,
                    "Alimentari": 400,
                    "Ristorazione": 150,
                    "Casa": 800,
                    "Salute": 100,
                    "Svago": 200,
                    "Abbigliamento": 100,
                    "Varie": 150
                },
                "entrate_mensili": 2500,
                "obiettivi": {
                    "risparmio_target": 500,
                    "alert_soglia_percentuale": 80
                }
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"✅ Creato {self.config_file}")
    
    def _load_config(self) -> Dict:
        """Carica configurazione da JSON"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Errore caricamento config: {e}")
            return {}
    
    def backup_data(self) -> bool:
        """Crea backup dei dati"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Backup CSV
            backup_csv = f"{self.backup_dir}/spese_backup_{timestamp}.csv"
            shutil.copy2(self.csv_file, backup_csv)
            
            # Backup config
            backup_config = f"{self.backup_dir}/config_backup_{timestamp}.json"
            shutil.copy2(self.config_file, backup_config)
            
            logger.info(f"💾 Backup creato: {timestamp}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore backup: {e}")
            return False
    
    def aggiungi_transazione(self, 
                            nome_transazione: str, 
                            categoria: str, 
                            importo: float, 
                            tipo: str = 'spesa',
                            note: str = "",
                            data: Optional[str] = None) -> bool:
        """
        Aggiunge una nuova transazione al CSV (spesa o ricavo)
        
        Args:
            nome_transazione: Descrizione della transazione
            categoria: Categoria (dipende dal tipo)
            importo: Importo in euro
            tipo: 'spesa' o 'ricavo'
            note: Note aggiuntive (opzionale)
            data: Data in formato YYYY-MM-DD (default: oggi)
        
        Returns:
            True se salvata con successo
        """
        try:
            if data is None:
                data = datetime.now().strftime("%Y-%m-%d")
            
            # Crea nuovo record
            nuovo_record = {
                'data': data,
                'nome_transazione': nome_transazione,
                'categoria': categoria,
                'importo': importo,
                'tipo': tipo,
                'note': note
            }
            
            return self._salva_record(nuovo_record)
            
        except Exception as e:
            logger.error(f"Errore aggiunta transazione: {e}")
            return False

    def aggiungi_spesa(self, 
                       nome_spesa: str, 
                       categoria: str, 
                       importo: float, 
                       note: str = "",
                       data: Optional[str] = None) -> bool:
        """
        Aggiunge una nuova spesa al CSV (retrocompatibilità)
        """
        return self.aggiungi_transazione(
            nome_transazione=nome_spesa,
            categoria=categoria,
            importo=importo,
            tipo='spesa',
            note=note,
            data=data
        )
    
    def _salva_record(self, record: dict) -> bool:
        """Salva un record nel CSV"""
        try:
            # Leggi CSV esistente
            if os.path.exists(self.csv_file):
                df = pd.read_csv(self.csv_file)
            else:
                # Crea nuovo CSV con header aggiornato
                df = pd.DataFrame(columns=['data', 'nome_transazione', 'categoria', 'importo', 'tipo', 'note'])
            
            # Aggiungi nuovo record
            df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
            
            # Salva CSV
            df.to_csv(self.csv_file, index=False)
            
            tipo_display = "ricavo" if record['tipo'] == 'ricavo' else "spesa"
            logger.info(f"💰 {tipo_display.title()} aggiunt{'o' if tipo_display == 'ricavo' else 'a'}: €{record['importo']:.2f} - {record['nome_transazione']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore salvataggio record: {e}")
            return False
    
    def get_spese_mese(self, anno: int = None, mese: int = None) -> pd.DataFrame:
        """Ottiene spese di un mese specifico"""
        try:
            df = pd.read_csv(self.csv_file)
            df['data'] = pd.to_datetime(df['data'])
            
            if anno is None:
                anno = datetime.now().year
            if mese is None:
                mese = datetime.now().month
            
            # Filtra per mese/anno
            mask = (df['data'].dt.year == anno) & (df['data'].dt.month == mese)
            return df[mask]
            
        except Exception as e:
            logger.error(f"❌ Errore lettura spese: {e}")
            return pd.DataFrame()
    
    def get_totale_per_categoria(self, anno: int = None, mese: int = None) -> Dict[str, float]:
        """Ottiene totale spese per categoria in un mese"""
        df = self.get_spese_mese(anno, mese)
        
        if df.empty:
            return {}
        
        totali = df.groupby('categoria')['importo'].sum().to_dict()
        return totali
    
    def verifica_budget(self, anno: int = None, mese: int = None) -> Dict:
        """
        Verifica stato budget vs spese reali
        
        Returns:
            Dict con budget, spese, differenze e alert
        """
        totali_categoria = self.get_totale_per_categoria(anno, mese)
        budget_mensile = self.config.get('budget_mensile', {})
        
        risultato = {
            'mese': f"{anno or datetime.now().year}-{mese or datetime.now().month:02d}",
            'categorie': {},
            'totale_budget': sum(budget_mensile.values()),
            'totale_spese': sum(totali_categoria.values()),
            'alert': []
        }
        
        # Analisi per categoria
        for categoria, budget in budget_mensile.items():
            speso = totali_categoria.get(categoria, 0)
            percentuale = (speso / budget * 100) if budget > 0 else 0
            
            risultato['categorie'][categoria] = {
                'budget': budget,
                'speso': speso,
                'rimanente': budget - speso,
                'percentuale': percentuale
            }
            
            # Alert se superata soglia
            soglia = self.config.get('obiettivi', {}).get('alert_soglia_percentuale', 80)
            if percentuale >= soglia:
                risultato['alert'].append(f"⚠️ {categoria}: {percentuale:.1f}% del budget")
        
        # Calcoli generali
        risultato['risparmio_reale'] = risultato['totale_budget'] - risultato['totale_spese']
        risultato['risparmio_target'] = self.config.get('obiettivi', {}).get('risparmio_target', 0)
        
        return risultato
    
    def get_statistiche_generali(self) -> Dict:
        """Ottiene statistiche generali sui dati"""
        try:
            df = pd.read_csv(self.csv_file)
            df['data'] = pd.to_datetime(df['data'])
            
            # Statistiche base
            stats = {
                'totale_records': len(df),
                'periodo': {
                    'da': df['data'].min().strftime("%Y-%m-%d") if not df.empty else None,
                    'a': df['data'].max().strftime("%Y-%m-%d") if not df.empty else None
                },
                'spesa_totale': df['importo'].sum(),
                'spesa_media': df['importo'].mean(),
                'categoria_piu_costosa': None,
                'mese_piu_costoso': None
            }
            
            if not df.empty:
                # Categoria più costosa
                cat_totali = df.groupby('categoria')['importo'].sum()
                stats['categoria_piu_costosa'] = cat_totali.idxmax()
                
                # Mese più costoso
                df['anno_mese'] = df['data'].dt.to_period('M')
                mese_totali = df.groupby('anno_mese')['importo'].sum()
                stats['mese_piu_costoso'] = str(mese_totali.idxmax())
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Errore statistiche: {e}")
            return {}

    def check_openai_credit(self) -> Dict:
        """
        Controlla le informazioni del credito OpenAI usando l'API usage corretta
        
        Returns:
            Dict con informazioni disponibili e stime
        """
        if not self.openai_api_key:
            return {"error": "API Key OpenAI non configurata nel file .env"}
        
        try:
            # Prima verifica se l'API key funziona
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_api_key)
            
            # Test connessione
            models = client.models.list()
            
            # Calcola timestamp per inizio mese (Unix timestamp)
            today = datetime.now()
            start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            start_timestamp = int(start_of_month.timestamp())
            
            # Chiamata API usage corretta
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            # Prova l'API usage per completions
            usage_url = f"https://api.openai.com/v1/organization/usage/completions"
            params = {
                'start_time': start_timestamp,
                'limit': 100  # Prendi gli ultimi 100 record
            }
            
            response = requests.get(usage_url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                usage_data = response.json()
                
                # Analizza i dati
                completions = usage_data.get('data', [])
                total_requests = len(completions)
                total_tokens = sum([c.get('n_context_tokens_total', 0) + c.get('n_generated_tokens_total', 0) for c in completions])
                
                # Stima costi (GPT-3.5-turbo pricing)
                input_cost = sum([c.get('n_context_tokens_total', 0) for c in completions]) / 1000 * 0.0005
                output_cost = sum([c.get('n_generated_tokens_total', 0) for c in completions]) / 1000 * 0.0015
                total_cost = input_cost + output_cost
                
                return {
                    "status": "success",
                    "api_key_valida": True,
                    "periodo_attuale": f"{start_of_month.strftime('%Y-%m-%d')} - {today.strftime('%Y-%m-%d')}",
                    "richieste_mese": total_requests,
                    "token_totali": total_tokens,
                    "costo_usd": f"${total_cost:.6f}",
                    "costo_eur": f"€{total_cost * 0.95:.6f}",
                    "modello_principale": "gpt-3.5-turbo",
                    "note": "Dati reali dall'API OpenAI Usage",
                    "dashboard_url": "https://platform.openai.com/usage",
                    "ultimo_controllo": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            
            elif response.status_code == 403:
                # Fallback: API key funziona ma non ha accesso all'usage
                return {
                    "status": "limited_access",
                    "api_key_valida": True,
                    "periodo_attuale": f"{start_of_month.strftime('%Y-%m-%d')} - {today.strftime('%Y-%m-%d')}",
                    "modelli_disponibili": len([m for m in models.data if "gpt" in m.id.lower()]),
                    "modello_principale": "gpt-3.5-turbo", 
                    "note": "API Key funzionante ma senza accesso usage - usa dashboard",
                    "dashboard_url": "https://platform.openai.com/usage",
                    "ultimo_controllo": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            
            else:
                return {"error": f"Errore API usage: {response.status_code} - {response.text[:200]}"}
            
        except Exception as e:
            error_msg = str(e)
            
            # Fallback con informazioni di base
            today = datetime.now()
            start_date = today.replace(day=1).strftime("%Y-%m-%d")
            
            if "invalid" in error_msg.lower() or "unauthorized" in error_msg.lower() or "401" in error_msg:
                status_msg = "❌ API Key non valida o scaduta"
            elif "quota" in error_msg.lower() or "exceeded" in error_msg.lower():
                status_msg = "⚠️ Quota OpenAI raggiunta"
            elif "billing" in error_msg.lower():
                status_msg = "💳 Problema di fatturazione"
            else:
                status_msg = "⚠️ Temporaneamente non disponibile"
            
            return {
                "status": "error_fallback",
                "api_key_valida": False,
                "periodo_attuale": f"{start_date} - {today.strftime('%Y-%m-%d')}",
                "note": f"{status_msg} - Verifica manualmente su dashboard",
                "dashboard_url": "https://platform.openai.com/usage",
                "ultimo_controllo": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "errore_tecnico": error_msg[:150] + "..." if len(error_msg) > 150 else error_msg
            }

    def stima_costo_mensile(self, richieste_al_giorno: int = 50) -> Dict:
        """
        Stima il costo mensile basato sull'usage stimato
        
        Args:
            richieste_al_giorno: Numero stimato di richieste bot al giorno
        
        Returns:
            Stima costi mensili
        """
        try:
            # Parametri stima per GPT-3.5-turbo
            token_medi_per_richiesta = 50  # Input + output medio per categorizzazione
            giorni_mese = 30
            
            richieste_mese = richieste_al_giorno * giorni_mese
            token_totali_mese = richieste_mese * token_medi_per_richiesta
            
            # Costo GPT-3.5-turbo (prezzi settembre 2024)
            costo_input = (token_totali_mese * 0.7) / 1000 * 0.0005   # 70% input, $0.0005/1k
            costo_output = (token_totali_mese * 0.3) / 1000 * 0.0015  # 30% output, $0.0015/1k
            costo_totale = costo_input + costo_output
            
            return {
                "richieste_giornaliere": richieste_al_giorno,
                "richieste_mensili": richieste_mese,
                "token_stimati_mese": token_totali_mese,
                "costo_mensile_usd": f"${costo_totale:.4f}",
                "costo_mensile_eur": f"€{costo_totale * 0.95:.4f}",
                "modello": "gpt-3.5-turbo",
                "note": "Stima basata su categorizzazione spese"
            }
            
        except Exception as e:
            return {"error": f"Errore stima costi: {e}"}

# Test rapido
if __name__ == "__main__":
    print("🧪 Test SpeseManager...")
    
    manager = SpeseManager()
    
    # Test aggiunta spesa
    success = manager.aggiungi_spesa(
        nome_spesa="Caffè del mattino",
        categoria="Ristorazione", 
        importo=2.50,
        note="Bar sotto casa"
    )
    
    if success:
        print("✅ Spesa aggiunta con successo")
        
        # Test statistiche
        stats = manager.get_statistiche_generali()
        print(f"📊 Records totali: {stats.get('totale_records', 0)}")
        
        # Test budget
        budget_info = manager.verifica_budget()
        print(f"💰 Spese questo mese: €{budget_info['totale_spese']:.2f}")
    
    else:
        print("❌ Errore nell'aggiunta della spesa")