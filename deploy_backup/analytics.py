#!/usr/bin/env python3
"""
📊 Sistema Analytics e Grafici per Spese
🎨 Matplotlib + Plotly per visualizzazioni
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import os

# Configurazione matplotlib per salvare immagini
plt.switch_backend('Agg')  # Backend non-interattivo per Telegram
sns.set_style("whitegrid")

class SpeseAnalytics:
    """Gestore analytics e grafici per spese"""
    
    def __init__(self, csv_file: str = "spese.csv", config_file: str = "config.json"):
        self.csv_file = csv_file
        self.config_file = config_file
        
        # Carica configurazione
        with open(config_file, 'r') as f:
            self.config = json.load(f)
            
        # Colori per categorie
        self.colori_categorie = {
            'Trasporti': '#FF6B6B',
            'Alimentari': '#4ECDC4', 
            'Ristorazione': '#45B7D1',
            'Casa': '#96CEB4',
            'Salute': '#FFEAA7',
            'Svago': '#DDA0DD',
            'Abbigliamento': '#98D8C8',
            'Varie': '#F7DC6F'
        }
    
    def _load_data(self) -> pd.DataFrame:
        """Carica e prepara i dati"""
        try:
            df = pd.read_csv(self.csv_file)
            df['data'] = pd.to_datetime(df['data'])
            df['anno_mese'] = df['data'].dt.to_period('M')
            df['mese_nome'] = df['data'].dt.strftime('%B %Y')
            return df
        except Exception as e:
            print(f"❌ Errore caricamento dati: {e}")
            return pd.DataFrame()
    
    def grafico_torta_categorie(self, mese: int = None, anno: int = None, save_path: str = "grafico_torta.png") -> str:
        """
        Crea grafico a torta per spese per categoria
        
        Returns:
            Path del file immagine salvato
        """
        df = self._load_data()
        
        if df.empty:
            return None
        
        # Filtra per mese/anno se specificati
        if mese and anno:
            df = df[(df['data'].dt.month == mese) & (df['data'].dt.year == anno)]
        elif not mese and not anno:
            # Usa mese corrente
            oggi = datetime.now()
            df = df[(df['data'].dt.month == oggi.month) & (df['data'].dt.year == oggi.year)]
        
        if df.empty:
            return None
        
        # Aggrega per categoria
        categorie = df.groupby('categoria')['importo'].sum()
        
        # Crea grafico
        fig, ax = plt.subplots(figsize=(10, 8))
        
        colors = [self.colori_categorie.get(cat, '#95A5A6') for cat in categorie.index]
        
        wedges, texts, autotexts = ax.pie(
            categorie.values,
            labels=categorie.index,
            autopct=lambda pct: f'€{categorie.sum() * pct / 100:.0f}\n({pct:.1f}%)',
            colors=colors,
            startangle=90
        )
        
        # Styling
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        periodo = f"{anno or datetime.now().year}-{mese or datetime.now().month:02d}"
        ax.set_title(f'💰 Spese per Categoria - {periodo}', fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return save_path
    
    def grafico_trend_mensile(self, save_path: str = "trend_mensile.png") -> str:
        """Grafico trend spese mensili"""
        df = self._load_data()
        
        if df.empty:
            return None
        
        # Aggrega per mese
        trend_mensile = df.groupby('anno_mese')['importo'].sum().reset_index()
        trend_mensile['mese_str'] = trend_mensile['anno_mese'].astype(str)
        
        # Crea grafico
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(
            range(len(trend_mensile)), 
            trend_mensile['importo'],
            marker='o',
            linewidth=2,
            markersize=8,
            color='#3498DB'
        )
        
        # Aggiungi valori sui punti
        for i, (idx, row) in enumerate(trend_mensile.iterrows()):
            ax.annotate(
                f'€{row["importo"]:.0f}',
                (i, row['importo']),
                textcoords="offset points",
                xytext=(0,10),
                ha='center',
                fontweight='bold'
            )
        
        ax.set_xticks(range(len(trend_mensile)))
        ax.set_xticklabels(trend_mensile['mese_str'], rotation=45)
        ax.set_title('📈 Trend Spese Mensili', fontsize=16, fontweight='bold')
        ax.set_ylabel('Importo (€)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return save_path
    
    def grafico_budget_vs_reale(self, mese: int = None, anno: int = None, save_path: str = "budget_vs_reale.png") -> str:
        """Grafico confronto budget vs spese reali"""
        df = self._load_data()
        
        if df.empty:
            return None
        
        # Filtra per mese
        if not mese:
            mese = datetime.now().month
        if not anno:
            anno = datetime.now().year
            
        df_mese = df[(df['data'].dt.month == mese) & (df['data'].dt.year == anno)]
        
        # Spese reali per categoria
        spese_reali = df_mese.groupby('categoria')['importo'].sum()
        
        # Budget configurato
        budget = self.config.get('budget_mensile', {})
        
        # Prepara dati per grafico
        categorie = list(budget.keys())
        budget_values = [budget.get(cat, 0) for cat in categorie]
        reali_values = [spese_reali.get(cat, 0) for cat in categorie]
        
        # Crea grafico
        x = range(len(categorie))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        bars1 = ax.bar([i - width/2 for i in x], budget_values, width, 
                      label='Budget', color='#2ECC71', alpha=0.8)
        bars2 = ax.bar([i + width/2 for i in x], reali_values, width,
                      label='Spese Reali', color='#E74C3C', alpha=0.8)
        
        # Aggiungi valori sulle barre
        for bar in bars1:
            height = bar.get_height()
            ax.annotate(f'€{height:.0f}', 
                       xy=(bar.get_x() + bar.get_width()/2, height),
                       xytext=(0, 3), textcoords="offset points",
                       ha='center', va='bottom', fontweight='bold')
        
        for bar in bars2:
            height = bar.get_height()
            ax.annotate(f'€{height:.0f}',
                       xy=(bar.get_x() + bar.get_width()/2, height),
                       xytext=(0, 3), textcoords="offset points", 
                       ha='center', va='bottom', fontweight='bold')
        
        ax.set_xlabel('Categorie', fontsize=12)
        ax.set_ylabel('Importo (€)', fontsize=12)
        ax.set_title(f'💰 Budget vs Spese Reali - {anno}-{mese:02d}', fontsize=16, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(categorie, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return save_path
    
    def grafico_spese_settimanali(self, save_path: str = "spese_settimanali.png") -> str:
        """Grafico spese per giorno della settimana"""
        df = self._load_data()
        
        if df.empty:
            return None
        
        # Ultimi 30 giorni
        oggi = datetime.now()
        un_mese_fa = oggi - timedelta(days=30)
        df_recente = df[df['data'] >= un_mese_fa]
        
        # Aggiungi giorno della settimana
        df_recente['giorno_settimana'] = df_recente['data'].dt.day_name()
        giorni_ord = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        giorni_ita = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
        
        # Mappa inglese -> italiano
        mapping_giorni = dict(zip(giorni_ord, giorni_ita))
        df_recente['giorno_ita'] = df_recente['giorno_settimana'].map(mapping_giorni)
        
        # Aggrega per giorno della settimana
        spese_giorno = df_recente.groupby('giorno_ita')['importo'].sum().reindex(giorni_ita, fill_value=0)
        
        # Crea grafico
        fig, ax = plt.subplots(figsize=(12, 6))
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8']
        
        bars = ax.bar(spese_giorno.index, spese_giorno.values, color=colors, alpha=0.8)
        
        # Valori sulle barre
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f'€{height:.0f}',
                           xy=(bar.get_x() + bar.get_width()/2, height),
                           xytext=(0, 3), textcoords="offset points",
                           ha='center', va='bottom', fontweight='bold')
        
        ax.set_title('📅 Spese per Giorno della Settimana (Ultimi 30 giorni)', fontsize=16, fontweight='bold')
        ax.set_ylabel('Importo (€)', fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return save_path
    
    def genera_report_completo(self) -> Dict[str, str]:
        """
        Genera tutti i grafici principali
        
        Returns:
            Dict con i path dei grafici generati
        """
        grafici = {}
        
        try:
            # Crea directory per i grafici
            os.makedirs("grafici", exist_ok=True)
            
            # Genera grafici
            grafici['torta'] = self.grafico_torta_categorie(save_path="grafici/torta_categorie.png")
            grafici['trend'] = self.grafico_trend_mensile(save_path="grafici/trend_mensile.png")
            grafici['budget'] = self.grafico_budget_vs_reale(save_path="grafici/budget_vs_reale.png")
            grafici['settimana'] = self.grafico_spese_settimanali(save_path="grafici/spese_settimanali.png")
            
            # Rimuovi valori None
            grafici = {k: v for k, v in grafici.items() if v is not None}
            
        except Exception as e:
            print(f"❌ Errore generazione grafici: {e}")
        
        return grafici

# Test del sistema
if __name__ == "__main__":
    print("🧪 Test Analytics...")
    
    analytics = SpeseAnalytics()
    
    # Genera grafici di test
    grafici = analytics.genera_report_completo()
    
    print(f"📊 Grafici generati: {len(grafici)}")
    for nome, path in grafici.items():
        print(f"  - {nome}: {path}")
    
    print("✅ Test completato!")