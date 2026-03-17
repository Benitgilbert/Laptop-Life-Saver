import os
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from supabase import create_client, Client
import json
import time

class AnomalyDetector:
    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initializes the AI Anomaly Detector.
        This runs on the Cloud Backend, NOT on the laptops, keeping the agent lightweight.
        """
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # The Isolation Forest model is perfect for finding hidden patterns in telemetry
        # that static rules/thresholds miss (e.g., high temp but low CPU usage = broken fan).
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.05, # We assume roughly 5% of data might be anomalous behavior
            random_state=42
        )
        self.is_trained = False

    def fetch_training_data(self, days=30) -> pd.DataFrame:
        """Fetch historical telemetry from Supabase across all devices for pattern learning."""
        print(f"Fetching last {days} days of telemetry data for AI training...")
        # In a real production scenario, we would filter by date.
        # For the prototype, we fetch a batch of recent telemetry.
        response = self.supabase.table('telemetry').select('*').limit(5000).execute()
        
        if not response.data:
            print("Not enough data to train the AI model.")
            return pd.DataFrame()
            
        df = pd.DataFrame(response.data)
        
        # We only want to train on the actual hardware metrics to find patterns
        features = ['cpu_usage_pct', 'cpu_temp_c', 'ram_usage_pct', 'disk_usage_pct', 'battery_percent']
        
        # Clean data (drop rows with missing critical metrics)
        df_clean = df.dropna(subset=features)
        
        # Return only the numerical feature columns for training
        return df_clean[features]

    def train_model(self):
        """Trains the Isolation Forest to understand 'Normal' vs 'Abnormal' laptop behavior."""
        df_train = self.fetch_training_data()
        
        if df_train.empty or len(df_train) < 50:
            print("⚠️ Insufficient data to train the ML model. The system needs more telemetry to study AI patterns.")
            return False
            
        print(f"Training Data Science Model on {len(df_train)} telemetry records...")
        
        # The model studies the correlations between CPU load, Temp, RAM, etc.
        self.model.fit(df_train)
        self.is_trained = True
        print("✅ AI Model successfully trained on historical patterns!")
        return True

    def analyze_latest_telemetry(self):
        """Analyzes the latest state of all devices and assigns an AI Health Score."""
        if not self.is_trained:
            print("Cannot analyze: Model is not trained yet.")
            return
            
        print("Running AI analysis on current active devices...")
        
        # Get all registered devices
        devices_response = self.supabase.table('devices').select('id, mac_address').execute()
        
        for device in devices_response.data:
            device_id = device['id']
            
            # Get the single most recent telemetry log for this device
            latest_tel = self.supabase.table('telemetry') \
                .select('*').eq('device_id', device_id).order('recorded_at', desc=True).limit(1).execute()
                
            if not latest_tel.data:
                continue
                
            tel_data = latest_tel.data[0]
            
            # Extract features matching the training shape
            features = ['cpu_usage_pct', 'cpu_temp_c', 'ram_usage_pct', 'disk_usage_pct', 'battery_percent']
            current_state = []
            
            for f in features:
                # Fallback to 0 if a metric is somehow missing
                val = tel_data.get(f)
                current_state.append(float(val) if val is not None else 0.0)
                
            df_current = pd.DataFrame([current_state], columns=features)
            
            # Predict Anomaly (-1 is anomaly, 1 is normal)
            prediction = self.model.predict(df_current)[0]
            
            # Calculate an "Anomaly Score" (negative values are more anomalous)
            # We map this to a friendly 0-100 "AI Health Score"
            raw_score = self.model.decision_function(df_current)[0]
            
            # Map raw score (typically between -0.5 and 0.5) to a 0-100 percentage
            # Normal behavior approaches 100%, highly anomalous approaches 0%
            normalized_score = float(max(0.0, min(100.0, ((raw_score + 0.5) * 100))))
            
            # Update the device's AI Health Score in the database
            self.supabase.table('devices').update({"health_score": round(normalized_score, 1)}).eq('id', device_id).execute()
            
            status = "🔴 ANOMALY DETECTED" if prediction == -1 else "🟢 NORMAL PATTERN"
            print(f"[{device['mac_address']}] AI Score: {normalized_score:.1f}% -> {status}")

if __name__ == "__main__":
    print("==================================================")
    print("Laptop Life-Saver: Data Science Prediction Engine")
    print("==================================================")
    
    # These should be loaded from an env file or config in production
    # Taking from the config file if available, or prompting the user
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "URL_PLACEHOLDER")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "KEY_PLACEHOLDER")
    
    # We will need to set these keys before running the script.
    print(f"Initializing ML Backend... [Requires Supabase Credentials]")
