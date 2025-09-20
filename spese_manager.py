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