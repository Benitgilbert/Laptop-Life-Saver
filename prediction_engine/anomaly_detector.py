import os
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from supabase import create_client, Client

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

    def fetch_training_data(self, limit: int = 5000) -> pd.DataFrame:
        """Fetch historical telemetry from Supabase across all devices for pattern learning."""
        import datetime
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=2)
        cutoff_iso = cutoff_date.isoformat()
        
        try:
            # Fetch telemetry within the last 2 days for AI training
            response = self.supabase.table('telemetry') \
                .select('*') \
                .gte('timestamp', cutoff_iso) \
                .order('timestamp', desc=True) \
                .limit(limit) \
                .execute()
        except Exception as e:
            print(f"Error connecting to Supabase: {e}")
            return pd.DataFrame()
        
        if not response.data:
            print("Not enough data to train the AI model.")
            return pd.DataFrame()
            
        df = pd.DataFrame(response.data)
        
        # We only want to train on the actual hardware metrics to find patterns
        features = ['cpu_percent', 'cpu_temp', 'ram_percent', 'disk_percent', 'battery_percent']
        
        # Some old data might not have battery_percent or cpu_temp, fill with Medians to save training
        for feature in features:
            if feature not in df.columns:
                df[feature] = 0.0
                
        df[features] = df[features].fillna(df[features].median())
        
        # Return only the numerical feature columns for training
        return df[features]

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
            
        print("\nRunning AI analysis on current active devices...")
        
        # Get all registered devices
        try:
            devices_response = self.supabase.table('devices').select('id, mac_address').execute()
        except Exception as e:
            print(f"Failed to fetch devices: {e}")
            return
            
        for device in devices_response.data:
            device_id = device['id']
            
            # Get the single most recent telemetry log for this device
            latest_tel = self.supabase.table('telemetry') \
                .select('*').eq('device_id', device_id).order('timestamp', desc=True).limit(1).execute()
                
            if not latest_tel.data:
                continue
                
            tel_data = latest_tel.data[0]
            
            # Extract features matching the training shape
            features = ['cpu_percent', 'cpu_temp', 'ram_percent', 'disk_percent', 'battery_percent']
            current_state = []
            
            for f in features:
                val = tel_data.get(f)
                current_state.append(float(val) if val is not None else 0.0)
                
            df_current = pd.DataFrame([current_state], columns=features)
            
            # Predict Anomaly (-1 is anomaly, 1 is normal)
            prediction = self.model.predict(df_current)[0]
            
            # Calculate an "Anomaly Score" (negative values are more anomalous)
            # We map this to a friendly 0-100 "AI Health Score"
            raw_score = self.model.decision_function(df_current)[0]
            
            # Map raw score (typically between -0.4 and 0.2 for Isolation Forest) to a 0-100 percentage
            # Normal behavior approaches 100%, highly anomalous approaches 0%
            normalized_score = float(max(0.0, min(100.0, ((raw_score + 0.3) / 0.5) * 100)))
            
            # Ensure it's a realistic percentage clamp
            if prediction == -1:
                normalized_score = min(normalized_score, 60.0) # Cap score if explicitly an anomaly
                
            # Update the device's AI Health Score in the database
            try:
                self.supabase.table('devices').update({"ai_health_score": round(normalized_score, 1)}).eq('id', device_id).execute()
                
                status = "🔴 ANOMALY DETECTED" if prediction == -1 else "🟢 NORMAL PATTERN"
                print(f"[{device['mac_address']}] AI Score: {normalized_score:.1f}% -> {status}")
            except Exception as e:
                print(f"Failed to update score for {device['mac_address']}: {e}")

if __name__ == "__main__":
    print("==================================================")
    print("Laptop Life-Saver: ML Prediction Engine")
    print("==================================================")
    
    # We will grab credentials from environment variables or prompt the user for them.
    # When deployed, the admin server will have these in a .env file.
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in your environment.")
        print("Please set them, or input them below for a quick test run:")
        SUPABASE_URL = input("Supabase URL: ").strip()
        SUPABASE_KEY = input("Supabase KEY: ").strip()

    if SUPABASE_URL and SUPABASE_KEY:
        detector = AnomalyDetector(SUPABASE_URL, SUPABASE_KEY)
        if detector.train_model():
            detector.analyze_latest_telemetry()
    else:
        print("Engine cannot run without Supabase credentials. Exiting.")
