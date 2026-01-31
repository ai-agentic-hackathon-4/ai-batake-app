import sys
import os
import logging
import json
from dotenv import load_dotenv

# Add path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from research_agent import perform_deep_research
    from db import save_growing_instructions, update_edge_agent_config, db
except ImportError:
    # Handle running from root
    sys.path.append(os.path.join(os.getcwd(), 'backend'))
    from backend.research_agent import perform_deep_research
    from backend.db import save_growing_instructions, update_edge_agent_config, db

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

def run_auto_process(vegetable_name, packet_info):
    print(f"=== Starting Auto-Process for '{vegetable_name}' ===")
    
    # 1. Deep Research
    print(f"\n[1/3] Performing Deep Research...")
    research_result = perform_deep_research(vegetable_name, packet_info)
    
    if "error" in research_result:
        print(f"[FAILURE] Research failed: {research_result['error']}")
        return

    print("Research completed successfully!")
    print(json.dumps(research_result, indent=2, ensure_ascii=False))

    # 2. Save to Vegetable Collection
    print(f"\n[2/3] Saving to Firestore (Vegetables Collection)...")
    try:
        doc_id = save_growing_instructions(vegetable_name, research_result)
        print(f"Saved with ID: {doc_id}")
    except Exception as e:
        print(f"[FAILURE] DB Save failed: {e}")

    # 3. Update Edge Agent Config
    print(f"\n[3/3] Updating Edge Agent Configuration...")
    try:
        update_edge_agent_config(research_result)
        print("Edge Agent Config updated.")
    except Exception as e:
        print(f"[FAILURE] Config Update failed: {e}")

    # 4. Verify
    print(f"\n[4/4] Verifying Final Config...")
    if db:
        doc = db.collection("configurations").document("edge_agent").get()
        if doc.exists:
            instruction = doc.to_dict().get("instruction", "")
            print("\n--- Edge Agent Instruction (Tail) ---")
            print(instruction[-300:])
            print("-------------------------------------")
            
            if vegetable_name in instruction:
                 print("\n✅ SUCCESS: Vegetable name found in edge config!")
            else:
                 print("\n⚠️ WARNING: Vegetable name NOT found in edge config.")
    else:
        print("Skipping verification (DB not connected)")

if __name__ == "__main__":
    target_veg = "小松菜"
    target_info = "暑さ寒さに強く、ほぼ一年中作れます。"
    run_auto_process(target_veg, target_info)
