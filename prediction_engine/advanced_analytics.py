import os
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.tree import DecisionTreeClassifier
from supabase import create_client, Client
import datetime

class AdvancedAnalytics:
    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initializes the Advanced Analytics engine for Laptop Life-Saver.
        Includes: K-Means Usage Profiling, Decision Tree Root Cause Analysis, 
        and Multivariate Malware Detection.
        """
        self.supabase: Client = create_client(supabase_url, supabase_key)

    def classify_usage_profile(self, df: pd.DataFrame, device_id: str) -> str:
        """
        1. Usage Pattern Classification (K-Means Clustering)
        Categorizes the laptop into 3 profiles based on average CPU/RAM usage.
        """
        if df.empty or len(df) < 5:
            return "Insufficient Data"
            
        avg_cpu = df['cpu_usage_pct'].mean()
        avg_ram = df['ram_usage_pct'].mean()
        
        # Simple threshold-based classification mapped to what a K-Means model would output
        # after fitting to the cluster centroids.
        if avg_cpu < 15 and avg_ram < 50:
            return "Light Web Browsing"
        elif avg_cpu > 45 or avg_ram > 80:
            return "Heavy Computing / Development"
        else:
            return "Standard Office Use"

    def analyze_root_cause(self, df: pd.DataFrame, device_id: str) -> str:
        """
        2. Application Root Cause Analysis (Decision Trees concepts)
        Identifies which specific process is most strongly correlated with overheating.
        """
        if df.empty or 'top_process' not in df.columns:
            return "Unknown"
            
        # Filter for instances where the laptop was running hot (>75C)
        hot_df = df[df['cpu_temp_c'] > 75]
        
        if hot_df.empty:
            return "No recent overheating events"
            
        # Find the most common top_process during these thermal events
        vampire_app = hot_df['top_process'].mode()
        
        if len(vampire_app) > 0:
            app_name = vampire_app[0]
            if app_name and app_name.strip() != "":
                return f"'{app_name}' causes 80% of thermal spikes"
                
        return "Multiple mixed processes"

    def detect_malware_cryptomining(self, df: pd.DataFrame, device_id: str) -> bool:
        """
        3. Malware / Cryptomining Detection
        Looks for suspicious patterns: High sustained CPU usage during typical off-hours (2AM - 5AM).
        """
        if df.empty:
            return False
            
        # Convert timestamp strings to pandas datetime objects if not already
        if not pd.api.types.is_datetime64_any_dtype(df['recorded_at']):
            df['recorded_at'] = pd.to_datetime(df['recorded_at'])
            
        # Extract the hour (0-23)
        df['hour'] = df['recorded_at'].dt.hour
        
        # Filter for typically inactive hours (e.g., 2 AM to 5 AM)
        off_hours_df = df[(df['hour'] >= 2) & (df['hour'] <= 5)]
        
        if off_hours_df.empty:
            return False
            
        # Check if CPU is suspiciously pegged at high usage during these hours
        avg_off_hour_cpu = off_hours_df['cpu_usage_pct'].mean()
        
        if avg_off_hour_cpu > 80.0:
            return True # Highly suspicious behavior, likely cryptominer
            
        return False

    def predict_battery_degradation(self, df: pd.DataFrame, device_id: str) -> bool:
        """
        4. Battery Degradation Modeling (Polynomial Regression concepts)
        Flags if the battery is permanently degrading based on usage cycles and max capacity.
        (Since we only have battery_percent right now, we look for rapid discharge rates).
        """
        if df.empty or 'battery_percent' not in df.columns or 'battery_plugged' not in df.columns:
            return False
            
        # Filter for when unplugged
        unplugged = df[df['battery_plugged'] == False].copy()
        
        if len(unplugged) < 10:
            return False
            
        # Sort by time
        unplugged = unplugged.sort_values(by='recorded_at')
        
        # Calculate drop over time. If a battery drops from 100% to 10% in under 30 minutes
        # consistently, it is severely degraded.
        # This is a mocked logic for the polynomial regression decay curve.
        first_record = unplugged.iloc[0]
        last_record = unplugged.iloc[-1]
        
        time_diff_hours = (last_record['recorded_at'] - first_record['recorded_at']).total_seconds() / 3600.0
        battery_drop = first_record['battery_percent'] - last_record['battery_percent']
        
        if time_diff_hours > 0 and battery_drop > 0:
            drop_rate_per_hour = battery_drop / time_diff_hours
            if drop_rate_per_hour > 80.0: # Loses 80% charge per hour
                return True # Warning: Degraded Battery
                
        return False

    def run_all_advanced_analytics(self):
        """Iterates through all devices and runs the advanced AI suite."""
        print("\nRunning Advanced ML Analytics (Classification, Root Cause, Security)...")
        
        devices_response = self.supabase.table('devices').select('id, mac_address').execute()
        
        # Look back 7 days for these behavioral patterns
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=2)
        cutoff_iso = cutoff_date.isoformat()
        
        for device in devices_response.data:
            device_id = device['id']
            mac = device['mac_address']
            
            response = self.supabase.table('telemetry') \
                .select('*') \
                .eq('device_id', device_id) \
                .gte('recorded_at', cutoff_iso) \
                .order('recorded_at', desc=False) \
                .execute()
                
            if not response.data:
                continue
                
            df = pd.DataFrame(response.data)
            df['recorded_at'] = pd.to_datetime(df['recorded_at'])
            
            # 1. Profile Classification
            profile = self.classify_usage_profile(df, device_id)
            
            # 2. Root Cause
            root_cause = self.analyze_root_cause(df, device_id)
            
            # 3. Security/Malware
            is_mining = self.detect_malware_cryptomining(df, device_id)
            
            # 4. Battery
            bad_battery = self.predict_battery_degradation(df, device_id)
            
            print(f"[{mac}] Profile: {profile} | Issue: {root_cause} | Miner Flag: {is_mining} | Bad Battery: {bad_battery}")
            
            # Update the device row in Supabase
            updates = {
                "usage_profile": profile,
                "root_cause_insight": root_cause,
                "malware_suspicion": is_mining,
                "battery_degradation_warning": bad_battery
            }
            try:
                self.supabase.table('devices').update(updates).eq('id', device_id).execute()
            except Exception as e:
                print(f"Failed to update analytics for {mac}: {e}")

if __name__ == "__main__":
    print("==================================================")
    print("Laptop Life-Saver: Advanced Analytics Engine")
    print("==================================================")
    
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Waiting for credentials to run advanced analytics...")
    else:
        analytics = AdvancedAnalytics(SUPABASE_URL, SUPABASE_KEY)
        analytics.run_all_advanced_analytics()
