import sys
import os
import logging
import json
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from research_agent import perform_deep_research
    from db import save_growing_instructions
except ImportError:
    # Fallback if running from root
    from backend.research_agent import perform_deep_research
    from backend.db import save_growing_instructions

def verify():
    vegetable = "枝豆"
    packet_info = "30cm間隔で点蒔き、鳥害に注意"
    
    print(f"--- Starting Deep Research Verification for {vegetable} ---")
    print(f"Packet Info: {packet_info}")
    
    result = perform_deep_research(vegetable, packet_info)
    
    print("\n--- Research Result ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if "error" in result:
        print("\n[FAILURE] Research returned error.")
        sys.exit(1)
    else:
        print("\n[SUCCESS] Research completed successfully.")
        
        print(f"\n--- Saving to Firestore ---")
        try:
            doc_id = save_growing_instructions(vegetable, result)
            print(f"[SUCCESS] Saved to Firestore with ID: {doc_id}")
            if "mock-id" in doc_id:
                print("Note: Saved with Mock ID (DB might be disabled or offline mode)")
        except Exception as e:
            print(f"[FAILURE] Could not save to Firestore: {e}")

if __name__ == "__main__":
    verify()
