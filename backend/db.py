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

def init_vegetable_status(vegetable_name: str) -> str:
    """Creates a document with 'processing' status."""
    if db is None: return "mock-id-processing"
    
    try:
        doc_ref = db.collection("vegetables").document()
        doc_ref.set({
            "name": vegetable_name,
            "created_at": datetime.now(),
            "status": "processing"
        })
        return doc_ref.id
    except Exception as e:
        logging.error(f"Error initializing status: {e}")
        return "error-id"

def update_vegetable_status(doc_id: str, status: str, data: dict = None):
    """Updates the status and optionally saves research data."""
    if db is None: return

    try:
        doc_ref = db.collection("vegetables").document(doc_id)
        update_data = {"status": status}
        if data:
            update_data["instructions"] = data
            
        doc_ref.update(update_data)
        logging.info(f"Updated doc {doc_id} to status {status}")
    except Exception as e:
        logging.error(f"Error updating status: {e}")

def get_all_vegetables():
    """Retrieves all vegetables sorted by creation date."""
    if db is None: return []

    try:
        docs = db.collection("vegetables").order_by("created_at", direction=firestore.Query.DESCENDING).stream()
        results = []
        for doc in docs:
            d = doc.to_dict()
            d['id'] = doc.id
            if 'created_at' in d and isinstance(d['created_at'], datetime):
                d['created_at'] = d['created_at'].isoformat()
            results.append(d)
        return results
    except Exception as e:
        logging.error(f"Error listing vegetables: {e}")
        return []

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

def update_edge_agent_config(research_data: dict):
    """
    Updates /configurations/edge_agent document with the specific system prompt 
    (complete_support_prompt) only. Overwrites existing instruction.
    """
    if db is None: return

    try:
        support_prompt = research_data.get("complete_support_prompt", "")
        # Fallback if complete_support_prompt is missing (e.g. older data or error)
        if not support_prompt:
             # Try constructing it from other fields
             name = research_data.get("name", "Unknown Plant")
             temp = research_data.get("optimal_temp_range", "")
             water = research_data.get("volumetric_water_content", "")
             support_prompt = f"【栽培データ: {name}】\n最適気温: {temp}\n水分基準: {water}"

        # Overwrite the instruction field directly with the support prompt
        doc_ref = db.collection("configurations").document("edge_agent")
        doc_ref.set({"instruction": support_prompt}, merge=True)
        logging.info("Updated edge_agent configuration with new research data (overwrite).")
        
    except Exception as e:
        logging.error(f"Error updating edge_agent config: {e}")

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
