#!/usr/bin/env python3
from google.cloud import firestore
import logging
from datetime import datetime

import google.auth.exceptions

# Initialize Firestore
# Note: Requires GOOGLE_CLOUD_PROJECT environment variable or ADC.
try:
    # db = google.cloud.firestore.Client()
    db = firestore.Client(project="ai-agentic-hackathon-4", database="ai-agentic-hackathon-4-db")
    logging.info("Firestore client initialized successfully.")
except google.auth.exceptions.DefaultCredentialsError:
    logging.warning("Firestore credentials not found. Running in offline mode (DB Disabled).")
    logging.warning("To enable DB, set GOOGLE_APPLICATION_CREDENTIALS or run 'gcloud auth application-default login'.")
    db = None
except Exception as e:
    logging.error(f"Failed to initialize Firestore client: {e}")
    db = None

def save_growing_instructions(vegetable_name: str, data: dict) -> str:
    """
    Saves the growing instructions to Firestore.
    
    Args:
        vegetable_name: Name of the vegetable (used as document ID or title).
        data: Dictionary containing growing instructions (temp, humidity, etc.).
        
    Returns:
        The ID of the saved document.
    """
    if db is None:
        logging.warning("Firestore is not available. Skipping save.")
        return "mock-id-firestore-unavailable"

    collection_name = "vegetables"
    
    try:
        # Create a document prompt. 
        # Using vegetable_name as ID might be risky if duplicates differ, 
        # but let's use it for easy lookup for now, or use auto-id.
        # Let's use auto-id but store name as field to allow multiple entries.
        
        doc_ref = db.collection(collection_name).document()
        
        save_data = {
            "name": vegetable_name,
            "created_at": datetime.now(),
            "instructions": data
        }
        
        doc_ref.set(save_data)
        logging.info(f"Saved instructions for {vegetable_name} with ID: {doc_ref.id}")
        return doc_ref.id
        
    except Exception as e:
        logging.error(f"Error saving to Firestore: {e}")
        raise e

def get_latest_vegetable():
    """
    Fetches the latest vegetable document from Firestore.
    """
    if db is None:
        logging.warning("Firestore is not available.")
        return None

    try:
        collection_name = "vegetables"
        # Order by created_at descending and limit to 1
        docs = db.collection(collection_name).order_by("created_at", direction=google.cloud.firestore.Query.DESCENDING).limit(1).stream()
        
        for doc in docs:
            return doc.to_dict()
            
        return None
        
    except Exception as e:
        logging.error(f"Error fetching from Firestore: {e}")
        return None

def get_recent_sensor_logs(limit: int = 5):
    """
    Fetches the recent sensor logs from Firestore.
    """
    if db is None:
        logging.warning("Firestore is not available.")
        return []

    try:
        collection_name = "sensor_logs"
        # Order by timestamp descending
        # Note: direction should be accessible via firestore.Query.DESCENDING or similar depending on import
        # We imported 'from google.cloud import firestore', so firestore.Query.DESCENDING is correct.
        docs = db.collection(collection_name).order_by("unix_timestamp", direction=firestore.Query.DESCENDING).limit(limit).stream()
        
        logs = []
        for doc in docs:
            log_data = doc.to_dict()
            log_data['id'] = doc.id
            logs.append(log_data)
            
        return logs
        
    except Exception as e:
        logging.error(f"Error fetching sensor logs from Firestore: {e}")
        return []

def get_sensor_history(hours: int = 24):
    """
    Fetches sensor logs for the specified number of past hours.
    Returns list sorted by timestamp ascending.
    """
    if db is None:
        logging.warning("Firestore is not available.")
        return []

    try:
        import time
        collection_name = "sensor_logs"
        
        # Calculate cutoff timestamp
        now = time.time()
        cutoff_time = now - (hours * 3600)
        
        # Query: specific range and order
        # Note: In Firestore, if you have a range filter on a field, you must order by that field first.
        docs = db.collection(collection_name)\
            .where("unix_timestamp", ">=", cutoff_time)\
            .order_by("unix_timestamp", direction=firestore.Query.ASCENDING)\
            .stream()
        
        logs = []
        for doc in docs:
            log_data = doc.to_dict()
            log_data['id'] = doc.id
            logs.append(log_data)
            
        return logs
        
    except Exception as e:
        logging.error(f"Error fetching sensor history from Firestore: {e}")
        return []

if __name__ == "__main__":
    if db:
        print("Testing Firestore Connection...")
        
        # Test get_recent_sensor_logs
        print("\n--- Recent Sensor Logs ---")
        logs = get_recent_sensor_logs(limit=60)
        for log in logs:
            print(f"Log ID: {log.get('id')}, Time: {log.get('timestamp')}, Temp: {log.get('temperature')}, Humidity: {log.get('humidity')}")

    else:
        print("Firestore client is not initialized.")
