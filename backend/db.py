from google.cloud import firestore
import logging
from datetime import datetime

# Initialize Firestore
try:
    db = firestore.Client(project="ai-agentic-hackathon-4", database="ai-agentic-hackathon-4-db")
    logging.info("Firestore client initialized successfully.")
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
        doc_ref = db.collection(collection_name).document()
        save_data = {
            "name": vegetable_name,
            "created_at": datetime.now(),
            "status": "completed",
            "instructions": data
        }
        doc_ref.set(save_data)
        logging.info(f"Saved instructions for {vegetable_name} with ID: {doc_ref.id}")
        return doc_ref.id
    except Exception as e:
        logging.error(f"Error saving to Firestore: {e}")
        raise e

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
            # Convert datetime to ISO string for JSON serialization
            if 'created_at' in d and isinstance(d['created_at'], datetime):
                d['created_at'] = d['created_at'].isoformat()
            results.append(d)
        return results
    except Exception as e:
        logging.error(f"Error listing vegetables: {e}")
        return []
