import sys
import os
import logging
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from research_agent import perform_deep_research
except ImportError:
    # Fallback if running from root
    from backend.research_agent import perform_deep_research

def verify():
    vegetable = "トマト"
    packet_info = "毎日水やり、日当たり良好な場所"
    
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

if __name__ == "__main__":
    verify()
