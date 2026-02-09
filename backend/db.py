#!/usr/bin/env python3
from google.cloud import firestore
from datetime import datetime

import google.auth.exceptions

# Import our structured logging module
try:
    from .logger import get_logger, info, debug, warning, error
except ImportError:
    from logger import get_logger, info, debug, warning, error

# Initialize logger
logger = get_logger()

# Initialize Firestore
# Note: Requires GOOGLE_CLOUD_PROJECT environment variable or ADC.
try:
    # db = google.cloud.firestore.Client()
    db = firestore.Client(project="ai-agentic-hackathon-4", database="ai-agentic-hackathon-4-db")
    info("Firestore client initialized successfully.")
except google.auth.exceptions.DefaultCredentialsError:
    warning("Firestore credentials not found. Running in offline mode (DB Disabled).")
    warning("To enable DB, set GOOGLE_APPLICATION_CREDENTIALS or run 'gcloud auth application-default login'.")
    db = None
except Exception as e:
    error(f"Failed to initialize Firestore client: {e}", exc_info=True)
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
        debug(f"Initialized vegetable status for {vegetable_name} with ID: {doc_ref.id}")
        return doc_ref.id
    except Exception as e:
        error(f"Error initializing status for {vegetable_name}: {e}", exc_info=True)
        return "error-id"

def update_vegetable_status(doc_id: str, status: str, data: dict = None):
    """Updates the status and optionally saves research data."""
    if db is None: return

    try:
        doc_ref = db.collection("vegetables").document(doc_id)
        update_data = {
            "status": status,
            "updated_at": datetime.now()
        }
        if data:
            update_data["instructions"] = data
            # Also merge into result field for frontend access
            # Get existing result first to preserve basic_analysis
            existing_doc = doc_ref.get()
            existing_result = {}
            if existing_doc.exists:
                existing_data = existing_doc.to_dict()
                existing_result = existing_data.get("result", {}) if existing_data else {}
            
            # Merge deep research into existing result
            merged_result = {**existing_result, **data}
            update_data["result"] = merged_result
            
        doc_ref.update(update_data)
        info(f"Updated doc {doc_id} to status {status}")
    except Exception as e:
        error(f"Error updating status for doc {doc_id}: {e}", exc_info=True)

def get_all_vegetables():
    """Retrieves all vegetables sorted by creation date."""
    if db is None: return []

    try:
        debug("Fetching all vegetables from Firestore")
        docs = db.collection("vegetables").order_by("created_at", direction=firestore.Query.DESCENDING).stream()
        results = []
        for doc in docs:
            d = doc.to_dict()
            d['id'] = doc.id
            if 'created_at' in d and isinstance(d['created_at'], datetime):
                d['created_at'] = d['created_at'].isoformat()
            results.append(d)
        debug(f"Retrieved {len(results)} vegetables")
        return results
    except Exception as e:
        error(f"Error listing vegetables: {e}", exc_info=True)
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
        warning("Firestore is not available. Skipping save.")
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
        info(f"Saved instructions for {vegetable_name} with ID: {doc_ref.id}")
        return doc_ref.id
        
    except Exception as e:
        error(f"Error saving instructions for {vegetable_name} to Firestore: {e}", exc_info=True)
        raise e

def get_latest_vegetable():
    """
    Fetches the latest vegetable document from Firestore.
    """
    if db is None:
        warning("Firestore is not available.")
        return None

    try:
        collection_name = "vegetables"
        debug("Fetching latest vegetable from Firestore")
        # Order by created_at descending and limit to 1
        docs = db.collection(collection_name).order_by("created_at", direction=google.cloud.firestore.Query.DESCENDING).limit(1).stream()
        
        for doc in docs:
            result = doc.to_dict()
            debug(f"Latest vegetable found: {result.get('name')}")
            return result
            
        debug("No vegetables found in Firestore")
        return None
        
    except Exception as e:
        error(f"Error fetching latest vegetable from Firestore: {e}", exc_info=True)
        return None

def update_edge_agent_config(research_data: dict):
    """
    Updates /configurations/edge_agent document with the specific system prompt 
    (complete_support_prompt) only. Overwrites existing instruction.
    """
    if db is None: return

    try:
        support_prompt = research_data.get("summary_prompt")
        if not support_prompt:
             support_prompt = research_data.get("complete_support_prompt", "")

        # Fallback if both are missing
        if not support_prompt:
             # Try constructing it from other fields
             name = research_data.get("name", "Unknown Plant")
             temp = research_data.get("optimal_temp_range", "")
             water = research_data.get("volumetric_water_content", "")
             support_prompt = f"【栽培データ: {name}】\n最適気温: {temp}\n水分基準: {water}"

        # Overwrite the instruction field directly with the support prompt
        doc_ref = db.collection("configurations").document("edge_agent")
        doc_ref.set({
            "instruction": support_prompt,
            "vegetable_name": research_data.get("name", "Unknown Plant"),
            "updated_at": datetime.now()
        }, merge=True)
        info(f"Updated edge_agent configuration with new research data for: {research_data.get('name', 'Unknown')}")
        
    except Exception as e:
        error(f"Error updating edge_agent config: {e}", exc_info=True)

def select_vegetable_instruction(doc_id: str) -> bool:
    """
    Selects a vegetable's instruction and applies it to the edge agent config.
    Returns True if successful, False otherwise.
    """
    if db is None: return False

    try:
        debug(f"Selecting vegetable instruction for doc: {doc_id}")
        doc_ref = db.collection("vegetables").document(doc_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            error(f"Vegetable doc {doc_id} not found.")
            return False
            
        data = doc.to_dict()
        instructions = data.get("instructions")
        
        if not instructions:
            error(f"Vegetable doc {doc_id} has no instructions.")
            return False
            
        # Add name to instructions if not present, for fallback in update_edge_agent_config
        if "name" not in instructions:
            instructions["name"] = data.get("name", "Unknown")
            
        update_edge_agent_config(instructions)
        info(f"Selected vegetable {doc_id} ({data.get('name')}) and updated agent config.")
        return True
        
    except Exception as e:
        error(f"Error selecting vegetable instruction for {doc_id}: {e}", exc_info=True)
        return False

def get_recent_sensor_logs(limit: int = 5):
    """
    Fetches the recent sensor logs from Firestore.
    """
    if db is None:
        warning("Firestore is not available.")
        return []

    try:
        collection_name = "sensor_logs"
        debug(f"Fetching recent {limit} sensor logs")
        # Order by timestamp descending
        # Note: direction should be accessible via firestore.Query.DESCENDING or similar depending on import
        # We imported 'from google.cloud import firestore', so firestore.Query.DESCENDING is correct.
        docs = db.collection(collection_name).order_by("unix_timestamp", direction=firestore.Query.DESCENDING).limit(limit).stream()
        
        logs = []
        for doc in docs:
            log_data = doc.to_dict()
            log_data['id'] = doc.id
            logs.append(log_data)
        
        debug(f"Retrieved {len(logs)} sensor logs")
        return logs
        
    except Exception as e:
        error(f"Error fetching sensor logs from Firestore: {e}", exc_info=True)
        return []

def get_sensor_history(hours: int = 24):
    """
    Fetches sensor logs for the specified number of past hours.
    Returns list sorted by timestamp ascending.
    """
    if db is None:
        warning("Firestore is not available.")
        return []

    try:
        import time
        collection_name = "sensor_logs"
        
        # Calculate cutoff timestamp
        now = time.time()
        cutoff_time = now - (hours * 3600)
        
        debug(f"Fetching sensor history for past {hours} hours (cutoff: {cutoff_time})")
        
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
        
        debug(f"Retrieved {len(logs)} sensor history records")
        return logs
        

    except Exception as e:
        error(f"Error fetching sensor history from Firestore: {e}", exc_info=True)
        return []

def get_agent_execution_logs(limit: int = 20):
    """
    Fetches the recent agent execution logs from Firestore.
    """
    if db is None:
        warning("Firestore is not available.")
        return []

    try:
        collection_name = "agent_execution_logs"
        debug(f"Fetching recent {limit} agent execution logs")
        # Order by unix_timestamp descending (assuming standard logging format)
        # If unix_timestamp doesn't exist, we might need to rely on 'timestamp' string or similar.
        # Let's try ordering by timestamp (ISO string) or unix_timestamp if available.
        # Based on user request, the collection is "agent_execution_logs".
        
        # Checking typical patterns, often logs have 'timestamp'.
        # Let's assume there is a 'timestamp' field.
        docs = db.collection(collection_name).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit).stream()
        
        logs = []
        for doc in docs:
            log_data = doc.to_dict()
            log_data['id'] = doc.id
            logs.append(log_data)
        
        debug(f"Retrieved {len(logs)} agent execution logs")
        return logs
        
    except Exception as e:
        error(f"Error fetching agent logs from Firestore: {e}", exc_info=True)
        return []

def save_seed_guide(data: dict, doc_id: str = None) -> str:
    """
    Saves or updates a seed guide to the 'saved_guides' collection.
    
    Args:
        data: Dictionary containing guide data.
        doc_id: Optional ID to update existing document.
        
    Returns:
        The ID of the saved document.
    """
    if db is None:
        warning("Firestore is not available. Skipping save.")
        return "mock-id-firestore-unavailable"

    collection_name = "seed_guide_jobs"
    
    try:
        save_data = data.copy()
        
        if doc_id:
            doc_ref = db.collection(collection_name).document(doc_id)
            save_data["updated_at"] = firestore.SERVER_TIMESTAMP
            doc_ref.set(save_data, merge=True)
            info(f"Updated seed guide with ID: {doc_id}")
            return doc_id
        else:
            save_data["created_at"] = firestore.SERVER_TIMESTAMP
            save_data["updated_at"] = firestore.SERVER_TIMESTAMP
            update_time, doc_ref = db.collection(collection_name).add(save_data)
            info(f"Created seed guide with ID: {doc_ref.id}")
            return doc_ref.id
        
    except Exception as e:
        error(f"Error saving seed guide to Firestore: {e}")
        raise e

def update_seed_guide_status(doc_id: str, status: str, message: str = None, result: list = None):
    """Updates the status of a seed guide."""
    if db is None: return

    try:
        doc_ref = db.collection("seed_guide_jobs").document(doc_id)
        update_data = {
            "status": status,
            "updated_at": datetime.now()
        }
        if message:
            update_data["message"] = message
        if result:
            update_data["steps"] = result
            
        doc_ref.set(update_data, merge=True)
        info(f"Updated guide {doc_id} status to {status}")
    except Exception as e:
        error(f"Error updating guide status: {e}")

def get_all_seed_guides():
    """Retrieves all saved seed guides sorted by creation date."""
    if db is None: return []

    try:
        docs = db.collection("seed_guide_jobs").order_by("created_at", direction=firestore.Query.DESCENDING).stream()
        results = []
        for doc in docs:
            d = doc.to_dict()
            d['id'] = doc.id
            if 'created_at' in d and isinstance(d['created_at'], datetime):
                d['created_at'] = d['created_at'].isoformat()
            if 'updated_at' in d and isinstance(d['updated_at'], datetime):
                d['updated_at'] = d['updated_at'].isoformat()
            results.append(d)
        return results
    except Exception as e:
        error(f"Error listing seed guides: {e}")
        return []

def get_seed_guide(doc_id: str):
    """Retrieves a specific seed guide by ID."""
    if db is None: return None
    
    try:
        doc_ref = db.collection("seed_guide_jobs").document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            d = doc.to_dict()
            d['id'] = doc.id
            if 'created_at' in d and isinstance(d['created_at'], datetime):
                d['created_at'] = d['created_at'].isoformat()
            if 'updated_at' in d and isinstance(d['updated_at'], datetime):
                d['updated_at'] = d['updated_at'].isoformat()
            return d
        return None
    except Exception as e:
        error(f"Error fetching seed guide {doc_id}: {e}")
        return None


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

def get_edge_agent_config() -> dict:
    """
    Retrieves the current edge agent configuration from Firestore.
    """
    if db is None:
        warning("Firestore is not available.")
        return {}

    try:
        doc_ref = db.collection("configurations").document("edge_agent")
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return {}
    except Exception as e:
        error(f"Error fetching edge agent config: {e}", exc_info=True)
        return {}
