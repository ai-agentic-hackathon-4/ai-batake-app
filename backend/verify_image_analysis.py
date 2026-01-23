import sys
import os
import logging
import json
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load env vars
load_dotenv()

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from research_agent import analyze_seed_packet, perform_deep_research
except ImportError:
    # Fallback if running from root
    from backend.research_agent import analyze_seed_packet, perform_deep_research

def verify_image(image_path: str):
    if not os.path.exists(image_path):
        print(f"[ERROR] File not found: {image_path}")
        return

    print(f"--- Starting Image Analysis for: {image_path} ---")
    
    # Read image
    with open(image_path, "rb") as f:
        image_bytes = f.read()
        
    # 1. Analyze
    print("[1] Analyzing seed packet...")
    analysis_result_json = analyze_seed_packet(image_bytes)
    print(f"Analysis Result: {analysis_result_json}")
    
    # Parse result
    try:
        # Simple cleanup if markdown code blocks are present
        clean_text = analysis_result_json.replace("```json", "").replace("```", "")
        analysis_data = json.loads(clean_text)
        vegetable_name = analysis_data.get("name", "Unknown")
        visible_instructions = analysis_data.get("visible_instructions", "")
    except Exception as e:
        print(f"[WARNING] Failed to parse analysis JSON: {e}")
        vegetable_name = "Unknown"
        visible_instructions = analysis_result_json
        
    print(f"Identified Vegetable: {vegetable_name}")
    print(f"Visible Instructions: {visible_instructions}")
    
    if vegetable_name == "Unknown":
        print("[FAILURE] Could not identify vegetable. Stopping.")
        return

    # 2. Deep Research
    print(f"\n[2] Performing Deep Research for {vegetable_name}...")
    research_result = perform_deep_research(vegetable_name, str(visible_instructions))
    
    print("\n--- Research Result ---")
    print(json.dumps(research_result, indent=2, ensure_ascii=False))
    
    if "error" in research_result:
        print(f"\n[FAILURE] Research returned error: {research_result['error']}")
    else:
        print("\n[SUCCESS] Image Analysis & Research completed successfully.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python backend/verify_image_analysis.py <path_to_image>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    verify_image(image_path)
