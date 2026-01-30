import sys
import os
import logging
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    from db import db
except ImportError:
    from backend.db import db

def verify_db_connection():
    print("--- Verifying Firestore Connection ---")
    
    if db is None:
        print("[FAILURE] Firestore client is NOT initialized (db is None).")
        print("Check your credentials and project configuration in backend/db.py.")
        return

    print("[SUCCESS] Firestore client object exists.")
    
    test_collection = "verification_test"
    test_doc_id = "test_connectivity"
    
    try:
        print(f"1. Attempting to write to collection '{test_collection}'...")
        doc_ref = db.collection(test_collection).document(test_doc_id)
        doc_ref.set({
            "message": "Hello Firestore",
            "timestamp": datetime.now()
        })
        print("[SUCCESS] Write successful.")
        
        print("2. Attempting to read the document back...")
        doc = doc_ref.get()
        if doc.exists:
            print(f"[SUCCESS] Read successful: {doc.to_dict()}")
        else:
            print("[FAILURE] Document written but not found on read.")
            
        print("3. Cleaning up (deleting test document)...")
        doc_ref.delete()
        print("[SUCCESS] Delete successful.")
        
        print("\n[OVERALL SUCCESS] Database connection is working correctly.")
        
    except Exception as e:
        print(f"\n[FAILURE] Database operation failed: {e}")

if __name__ == "__main__":
    verify_db_connection()
