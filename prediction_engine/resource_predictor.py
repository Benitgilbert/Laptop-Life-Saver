import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from supabase import create_client, Client
import datetime

class ResourcePredictor:
    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initializes the ML Resource Predictor (Linear Regression).
        This service predicts the Remaining Useful Life (RUL) of finite resources like Disk Space.
        """
        self.supabase: Client = create_client(supabase_url, supabase_key)

    def predict_days_until_disk_full(self, device_id: str, days_history: int = 14) -> int:
        """
        Analyzes the historical trend of disk usage for a specific device.
        Uses Line-of-Best-Fit (Linear Regression) to predict exactly how many days
        remain until the disk hits 100% capacity.
        """
        # Calculate the timestamp for `days_history` ago
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_history)
        cutoff_iso = cutoff_date.isoformat()
        
        # Fetch the telemetry for this specific device
        response = self.supabase.table('telemetry') \
            .select('timestamp, disk_percent') \
            .eq('device_id', device_id) \
            .gte('timestamp', cutoff_iso) \
            .order('timestamp', desc=False) \
            .execute()
            
        if not response.data or len(response.data) < 10:
            return -1 # Not enough data points to make a mathematically sound prediction
            
        df = pd.DataFrame(response.data)
        
        # Convert timestamp strings to pandas datetime objects
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Convert datetime to a numerical format for Regression (e.g., hours since the first log)
        min_time = df['timestamp'].min()
        df['hours_passed'] = (df['timestamp'] - min_time).dt.total_seconds() / 3600.0
        
        # Prepare X (Time) and y (Disk Usage)
        X = df[['hours_passed']].values
        y = df['disk_percent'].values
        
        # Train the Linear Regression model on this specific device's history
        model = LinearRegression()
        model.fit(X, y)
        
        # The slope (coefficient) tells us how fast the disk is filling up per hour
        growth_rate_per_hour = model.coef_[0]
        
        if growth_rate_per_hour <= 0.001:
            # Disk usage is stable or decreasing. No imminent failure predicted.
            return 999 
            
        # Get the very last known disk usage and time
        current_disk_usage = y[-1]
        current_hour = X[-1][0]
        
        # Algebra: y = mx + b  ->  (Target - Current_Y) / m = Hours Left
        # We want to know when it hits 99% usage
        target_usage = 99.0
        
        if current_disk_usage >= target_usage:
            return 0 # Already full!
            
        hours_until_full = (target_usage - current_disk_usage) / growth_rate_per_hour
        days_until_full = int(hours_until_full / 24)
        
        return max(0, days_until_full)

    def run_all_predictions(self):
        """Iterates through all devices and updates their predictive metrics."""
        print("\nRunning ML Disk Exhaustion Predictions...")
        
        devices_response = self.supabase.table('devices').select('id, mac_address').execute()
        
        for device in devices_response.data:
            device_id = device['id']
            mac = device['mac_address']
            
            days_left = self.predict_days_until_disk_full(device_id)
            
            if days_left == -1:
                print(f"[{mac}] Insufficient historical data for regression prediction.")
                # Clear the column if we can't predict anymore
                self.supabase.table('devices').update({"predicted_disk_full_days": None}).eq('id', device_id).execute()
            elif days_left == 999:
                print(f"[{mac}] Storage growth is stable (No predicted exhaustion).")
                self.supabase.table('devices').update({"predicted_disk_full_days": 999}).eq('id', device_id).execute()
            else:
                alert = "⚠️ WARNING" if days_left < 14 else "ℹ️ OK"
                print(f"[{mac}] {alert}: AI predicts disk will be full in {days_left} days.")
                self.supabase.table('devices').update({"predicted_disk_full_days": days_left}).eq('id', device_id).execute()

if __name__ == "__main__":
    print("==================================================")
    print("Laptop Life-Saver: Resource Exhaustion Predictor")
    print("==================================================")
    
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Waiting for credentials to run tests...")
    else:
        predictor = ResourcePredictor(SUPABASE_URL, SUPABASE_KEY)
        predictor.run_all_predictions()
