import os
import logging
from dotenv import load_dotenv
from prediction_engine.anomaly_detector import AnomalyDetector
from prediction_engine.resource_predictor import ResourcePredictor
from prediction_engine.advanced_analytics import AdvancedAnalytics

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CloudMLRunner")

def run_ml_pipeline():
    load_dotenv()
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        logger.error("Missing SUPABASE_URL or SUPABASE_KEY environment variables.")
        return

    logger.info("Starting Laptop Life-Saver Cloud ML Pipeline...")

    # 1. Anomaly Detection (Isolation Forest)
    try:
        logger.info("Initializing Anomaly Detector...")
        detector = AnomalyDetector(url, key)
        if detector.train_model():
            detector.analyze_latest_telemetry()
    except Exception as e:
        logger.error(f"Anomaly Detection failed: {e}")

    # 2. Resource Exhaustion Prediction (Linear Regression)
    try:
        logger.info("Initializing Resource Predictor...")
        predictor = ResourcePredictor(url, key)
        predictor.run_all_predictions()
    except Exception as e:
        logger.error(f"Resource Prediction failed: {e}")

    # 3. Advanced Behavioral Analytics (K-Means, Root Cause, etc.)
    try:
        logger.info("Initializing Advanced Analytics Engine...")
        analytics = AdvancedAnalytics(url, key)
        analytics.run_all_advanced_analytics()
    except Exception as e:
        logger.error(f"Advanced Analytics failed: {e}")

    logger.info("Cloud ML Pipeline execution complete.")

if __name__ == "__main__":
    run_ml_pipeline()
