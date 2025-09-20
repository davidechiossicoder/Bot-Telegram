#!/usr/bin/env python3
"""
🤖 Sistema AI per Predizioni Finanziarie
🧠 Scikit-learn per analisi predittiva delle spese
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import json
import warnings
from typing import Dict, List
warnings.filterwarnings('ignore')

class SpeseAI:
    """Sistema AI per predizioni e analisi delle spese"""
    
    def __init__(self, csv_file: str = "spese.csv", config_file: str = "config.json"):
        self.csv_file = csv_file
        self.config_file = config_file
        
        # Modelli
        self.model_totale = RandomForestRegressor(n_estimators=50, random_state=42)
        self.models_categoria = {}
        
        # Encoders
        self.label_encoder = LabelEncoder()
        
    def _load_and_prepare_data(self) -> pd.DataFrame:
        """Carica e prepara dati per ML"""
        try:
            df = pd.read_csv(self.csv_file)
            df['data'] = pd.to_datetime(df['data'])
            
            # Features temporali
            df['anno'] = df['data'].dt.year
            df['mese'] = df['data'].dt.month
            df['giorno'] = df['data'].dt.day
            df['giorno_settimana'] = df['data'].dt.dayofweek
            df['giorno_anno'] = df['data'].dt.dayofyear
            
            # Encode categoria
            if 'categoria' in df.columns:
                df['categoria_encoded'] = self.label_encoder.fit_transform(df['categoria'])
            
            return df
            
        except Exception as e:
            print(f"❌ Errore preparazione dati: {e}")
            return pd.DataFrame()
    
    def train_modello_spesa_totale(self) -> Dict:
        """
        Addestra modello per predire spesa totale mensile
        
        Returns:
            Dict con metriche di performance del modello
        """
        df = self._load_and_prepare_data()
        
        if len(df) < 10:  # Dati insufficienti
            return {"errore": "Dati insufficienti per training (min 10 records)"}
        
        # Aggrega per mese
        df_mensile = df.groupby(['anno', 'mese']).agg({
            'importo': 'sum',
            'giorno_settimana': 'mean',  # Giorno medio della settimana
            'categoria_encoded': lambda x: x.mode().iloc[0] if not x.empty else 0  # Categoria più frequente
        }).reset_index()
        
        if len(df_mensile) < 3:  # Serve almeno 3 mesi
            return {"errore": "Servono almeno 3 mesi di dati"}
        
        # Features per training
        features = ['anno', 'mese', 'giorno_settimana', 'categoria_encoded']
        X = df_mensile[features]
        y = df_mensile['importo']
        
        # Train model
        if len(X) > 3:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
            
            self.model_totale.fit(X_train, y_train)
            
            # Metriche
            y_pred = self.model_totale.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            return {
                "success": True,
                "mae": mae,
                "r2": r2,
                "samples_train": len(X_train),
                "samples_test": len(X_test)
            }
        else:
            # Troppi pochi dati per split, usa tutti per training
            self.model_totale.fit(X, y)
            return {
                "success": True,
                "mae": "N/A (dati limitati)",
                "r2": "N/A (dati limitati)", 
                "samples_train": len(X),
                "samples_test": 0
            }
    
    def predici_spesa_mese_prossimo(self) -> Dict:
        """
        Predice spesa totale del mese prossimo
        
        Returns:
            Dict con predizione e confidence interval
        """
        try:
            # Prossimo mese
            prossimo_mese = datetime.now() + timedelta(days=30)
            anno = prossimo_mese.year
            mese = prossimo_mese.month
            
            # Features per predizione
            features = np.array([[
                anno,
                mese,
                3,  # Giorno settimana medio (mercoledì)
                0   # Categoria più frequente (approssimazione)
            ]])
            
            # Predizione
            predizione = self.model_totale.predict(features)[0]
            
            # Confidence interval approssimato (±20%)
            confidence_low = predizione * 0.8
            confidence_high = predizione * 1.2
            
            return {
                "success": True,
                "mese": f"{anno}-{mese:02d}",
                "predizione": predizione,
                "range_min": confidence_low,
                "range_max": confidence_high,
                "confidence": "80%"
            }
            
        except Exception as e:
            return {"errore": f"Errore predizione: {e}"}
    
    def analizza_pattern_spesa(self) -> Dict:
        """Analizza pattern e tendenze nelle spese"""
        df = self._load_and_prepare_data()
        
        if df.empty:
            return {"errore": "Nessun dato disponibile"}
        
        analisi = {}
        
        try:
            # Spesa media per giorno della settimana
            giorni = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
            spesa_per_giorno = df.groupby('giorno_settimana')['importo'].mean()
            
            analisi['spesa_per_giorno'] = {
                giorni[i]: spesa_per_giorno.get(i, 0) for i in range(7)
            }
            
            # Giorno più costoso
            giorno_max = spesa_per_giorno.idxmax()
            analisi['giorno_piu_costoso'] = giorni[giorno_max]
            
            # Trend mensile
            df_mensile = df.groupby(['anno', 'mese'])['importo'].sum()
            if len(df_mensile) > 1:
                trend = df_mensile.pct_change().mean() * 100
                analisi['trend_mensile_percentuale'] = trend
                analisi['trend_direzione'] = 'crescente' if trend > 0 else 'decrescente'
            
            # Categoria più costosa
            cat_totali = df.groupby('categoria')['importo'].sum()
            analisi['categoria_piu_costosa'] = cat_totali.idxmax()
            analisi['percentuale_categoria_top'] = (cat_totali.max() / cat_totali.sum()) * 100
            
            # Spesa media mensile
            analisi['spesa_media_mensile'] = df_mensile.mean() if not df_mensile.empty else 0
            
            # Volatilità (standard deviation)
            analisi['volatilita'] = df_mensile.std() if len(df_mensile) > 1 else 0
            
            return analisi
            
        except Exception as e:
            return {"errore": f"Errore analisi: {e}"}
    
    def raccomandazioni_budget(self) -> List[str]:
        """Genera raccomandazioni per ottimizzare il budget"""
        df = self._load_and_prepare_data()
        
        if df.empty:
            return ["Nessun dato disponibile per raccomandazioni"]
        
        raccomandazioni = []
        
        try:
            # Carica config budget
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            budget = config.get('budget_mensile', {})
            
            # Analisi per categoria
            oggi = datetime.now()
            df_mese = df[(df['data'].dt.month == oggi.month) & (df['data'].dt.year == oggi.year)]
            
            spese_categoria = df_mese.groupby('categoria')['importo'].sum()
            
            for categoria, budget_cat in budget.items():
                spesa_reale = spese_categoria.get(categoria, 0)
                percentuale = (spesa_reale / budget_cat * 100) if budget_cat > 0 else 0
                
                if percentuale > 90:
                    raccomandazioni.append(f"🚨 {categoria}: Budget quasi esaurito ({percentuale:.0f}%)")
                elif percentuale > 75:
                    raccomandazioni.append(f"⚠️ {categoria}: Attenzione al budget ({percentuale:.0f}%)")
                elif percentuale < 50:
                    raccomandazioni.append(f"✅ {categoria}: Budget sotto controllo ({percentuale:.0f}%)")
            
            # Raccomandazioni generali
            pattern = self.analizza_pattern_spesa()
            
            if 'giorno_piu_costoso' in pattern:
                giorno = pattern['giorno_piu_costoso']
                raccomandazioni.append(f"📊 Tendi a spendere di più il {giorno}")
            
            if 'trend_direzione' in pattern:
                if pattern['trend_direzione'] == 'crescente':
                    raccomandazioni.append("📈 Le tue spese sono in aumento, considera di rivedere il budget")
                else:
                    raccomandazioni.append("📉 Ottimo! Le tue spese sono in diminuzione")
            
            # Suggerimenti basati su volatilità
            if 'volatilita' in pattern and pattern['volatilita'] > 100:
                raccomandazioni.append("🎢 Le tue spese sono molto variabili, considera un budget più flessibile")
            
            return raccomandazioni[:5]  # Max 5 raccomandazioni
            
        except Exception as e:
            return [f"❌ Errore generazione raccomandazioni: {e}"]
    
    def detecta_anomalie(self, soglia: float = 2.0) -> List[Dict]:
        """
        Detecta spese anomale (outliers)
        
        Args:
            soglia: Numero di deviazioni standard per considerare anomalia
            
        Returns:
            Lista di spese anomale
        """
        df = self._load_and_prepare_data()
        
        if df.empty:
            return []
        
        anomalie = []
        
        try:
            # Per ogni categoria, trova outliers
            for categoria in df['categoria'].unique():
                df_cat = df[df['categoria'] == categoria]
                
                if len(df_cat) < 3:  # Servono almeno 3 dati
                    continue
                
                mean_cat = df_cat['importo'].mean()
                std_cat = df_cat['importo'].std()
                
                # Soglia anomalia
                soglia_sup = mean_cat + (soglia * std_cat)
                
                # Trova anomalie
                outliers = df_cat[df_cat['importo'] > soglia_sup]
                
                for _, row in outliers.iterrows():
                    anomalie.append({
                        'data': row['data'].strftime('%Y-%m-%d'),
                        'nome': row['nome_spesa'],
                        'categoria': row['categoria'],
                        'importo': row['importo'],
                        'media_categoria': mean_cat,
                        'differenza': row['importo'] - mean_cat
                    })
            
            # Ordina per importo decrescente
            anomalie.sort(key=lambda x: x['importo'], reverse=True)
            
            return anomalie[:10]  # Max 10 anomalie
            
        except Exception as e:
            print(f"❌ Errore detection anomalie: {e}")
            return []

# Test sistema AI
if __name__ == "__main__":
    print("🤖 Test Sistema AI...")
    
    ai = SpeseAI()
    
    # Training del modello
    print("🏋️ Training modello...")
    risultato_training = ai.train_modello_spesa_totale()
    print(f"📊 Risultato training: {risultato_training}")
    
    # Predizione mese prossimo
    print("🔮 Predizione mese prossimo...")
    predizione = ai.predici_spesa_mese_prossimo()
    print(f"💰 Predizione: {predizione}")
    
    # Analisi pattern
    print("📈 Analisi pattern...")
    pattern = ai.analizza_pattern_spesa()
    print(f"🔍 Pattern: {list(pattern.keys())}")
    
    # Raccomandazioni
    print("💡 Raccomandazioni...")
    raccomandazioni = ai.raccomandazioni_budget()
    for i, racc in enumerate(raccomandazioni, 1):
        print(f"  {i}. {racc}")
    
    # Anomalie
    print("🚨 Anomalie...")
    anomalie = ai.detecta_anomalie()
    print(f"⚠️ Trovate {len(anomalie)} anomalie")
    
    print("✅ Test AI completato!")