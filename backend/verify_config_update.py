import sys
import os
import logging
try:
    from backend.db import update_edge_agent_config, db
except ImportError:
    from db import update_edge_agent_config, db

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def verify_config_update():
    print("--- Verifying Edge Agent Config Update ---")
    
    # 1. Update Config with Mock Data
    print("1. Updating configuration with mock data...")
    mock_research_data = {
        "name": "テスト用トマト",
        "complete_support_prompt": "【テスト用指示】\nトマトは日当たりを好みます。体積含水率は20%前後を維持してください。"
    }
    
    try:
        update_edge_agent_config(mock_research_data)
        print("[SUCCESS] Update function called successfully.")
    except Exception as e:
        print(f"[FAILURE] Func call failed: {e}")
        return

    # 2. Check Firestore
    print("2. Fetching document from Firestore to verify...")
    try:
        doc_ref = db.collection("configurations").document("edge_agent")
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            instruction = data.get("instruction", "")
            print("\n--- Current Instruction ---")
            print(instruction[:200] + "...\n(truncated)\n" + instruction[-200:])
            print("---------------------------")
            
            # Verify that the instruction is ONLY the research content (or starts with it)
            # and DOES NOT contain the old base instruction "マルチモーダルアシスタント"
            if "テスト用トマト" in instruction and "マルチモーダルアシスタント" not in instruction:
                 print("\n[SUCCESS] Configuration updated correctly (Overwrite confirmed)!")
            else:
                 print("\n[FAILURE] Content mismatch. Found base instruction or missing new data.")
        else:
            print("[FAILURE] Document does not exist.")
            
    except Exception as e:
        print(f"[FAILURE] Verification failed: {e}")

if __name__ == "__main__":
    verify_config_update()
