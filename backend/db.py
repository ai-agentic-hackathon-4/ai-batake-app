import google.cloud.firestore
import logging
from datetime import datetime

import google.auth.exceptions

# Initialize Firestore
# Note: Requires GOOGLE_CLOUD_PROJECT environment variable or ADC.
try:
    db = google.cloud.firestore.Client()
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
