from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
import logging
import os
import json
from dotenv import load_dotenv

try:
    from .db import init_vegetable_status, update_vegetable_status, get_all_vegetables
    from .research_agent import analyze_seed_packet, perform_deep_research
except ImportError:
    # When running directly as a script
    from db import init_vegetable_status, update_vegetable_status, get_all_vegetables
    from research_agent import analyze_seed_packet, perform_deep_research

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

app = FastAPI()

def process_research(doc_id: str, vegetable_name: str, analysis_data: dict):
    """
    Background task to perform heavy deep research and update DB.
    """
    logging.info(f"[Background] Starting research for {vegetable_name} (ID: {doc_id})")
    try:
        # Perform Deep Research
        research_result = perform_deep_research(vegetable_name, str(analysis_data))
        
        # Merge analysis data (like original instructions) if needed, 
        # or just save what research returned.
        # Let's ensure 'visible_instructions' is preserved if research fails or as extra info.
        if isinstance(research_result, dict):
            research_result["original_analysis"] = analysis_data
        
        # Update DB to completed
        update_vegetable_status(doc_id, "completed", research_result)
        logging.info(f"[Background] Research completed for {vegetable_name}")
        
    except Exception as e:
        logging.error(f"[Background] Research failed for {vegetable_name}: {e}")
        update_vegetable_status(doc_id, "failed", {"error": str(e)})

@app.post("/api/register-seed")
async def register_seed(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Receives image, starts async research, returns ID immediately.
    """
    try:
        # Read image
        content = await file.read()
        
        # 1. Analyze Seed Packet (Sync - Fast enough, usu. 2-5s)
        logging.info("Analyzing seed packet image...")
        packet_analysis_json = analyze_seed_packet(content)
        
        # Parse analysis result
        try:
            clean_text = packet_analysis_json.replace("```json", "").replace("```", "")
            analysis_data = json.loads(clean_text)
            vegetable_name = analysis_data.get("name", "Unknown Vegetable")
        except:
            vegetable_name = "Unknown Vegetable"
            analysis_data = {"raw": packet_analysis_json}
            
        logging.info(f"Identified vegetable: {vegetable_name}")
        
        # 2. Initialize DB Document (Status: processing)
        doc_id = init_vegetable_status(vegetable_name)
        
        # 3. Queue Background Task
        background_tasks.add_task(process_research, doc_id, vegetable_name, analysis_data)
        
        return {
            "status": "accepted",
            "message": "Research started in background",
            "document_id": doc_id,
            "vegetable": vegetable_name,
            "initial_analysis": analysis_data
        }
        
    except Exception as e:
        logging.error(f"Error in register_seed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vegetables")
async def list_vegetables():
    """Returns list of all vegetables with current status."""
    return get_all_vegetables()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
