from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
import os
import logging
import base64
import json
from google.cloud import storage
from google.cloud import firestore
from dotenv import load_dotenv

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

# Imports
try:
    # Try importing from feature/#3 db functions
    from .db import init_vegetable_status, update_vegetable_status, get_all_vegetables, update_edge_agent_config, get_latest_vegetable, get_sensor_history, get_recent_sensor_logs, get_agent_execution_logs
    # Also old ones just in case
    from .db import save_growing_instructions, save_seed_guide, get_all_seed_guides, get_seed_guide, update_seed_guide_status
    from .research_agent import analyze_seed_packet, perform_deep_research
    from .agent import get_weather_from_agent
except ImportError:
    # When running directly as a script
    from db import init_vegetable_status, update_vegetable_status, get_all_vegetables, update_edge_agent_config, get_latest_vegetable, get_sensor_history, get_recent_sensor_logs, save_growing_instructions, get_agent_execution_logs, save_seed_guide, get_all_seed_guides, get_seed_guide, update_seed_guide_status
    from research_agent import analyze_seed_packet, perform_deep_research
    from agent import get_weather_from_agent

# Imports from feature/#5 (Async/New)
try:
    from .seed_service import analyze_seed_and_generate_guide
except ImportError:
    try:
        from seed_service import analyze_seed_and_generate_guide
    except ImportError as e:
        logging.warning(f"Failed to import seed_service: {e}")
        pass

app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Firestore Client (Async)
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
db = firestore.AsyncClient(project=project_id, database="ai-agentic-hackathon-4-db")
COLLECTION_NAME = "seed_guide_jobs"

class WeatherRequest(BaseModel):
    region: str

@app.post("/api/weather")
async def get_weather(request: WeatherRequest):
    try:
        weather_info = get_weather_from_agent(request.region)
        return {"message": weather_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sensors/latest")
async def get_latest_sensor_log_endpoint():
    try:
        logs = get_recent_sensor_logs(limit=1)
        if logs and len(logs) > 0:
            return logs[0]
        return {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sensor-history")
async def get_sensor_history_endpoint(hours: int = 24):
    try:
        data = get_sensor_history(hours=hours)
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vegetables/latest")
async def get_latest_vegetable_endpoint():
    try:
        data = get_latest_vegetable()
        if data:
            return data
        else:
            return {} 

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agent-logs")
async def get_agent_logs_endpoint():
    try:
        logs = get_agent_execution_logs(limit=20)
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- feature/#3 Endpoints (Research Agent UI Support) ---

def process_research(doc_id: str, vegetable_name: str, analysis_data: dict):
    """
    Background task to perform heavy deep research and update DB.
    """
    logging.info(f"[Background] Starting research for {vegetable_name} (ID: {doc_id})")
    try:
        # Perform Deep Research
        research_result = perform_deep_research(vegetable_name, str(analysis_data))
        
        # Merge analysis data (like original instructions) if needed
        if isinstance(research_result, dict):
            research_result["original_analysis"] = analysis_data
        
        # Update DB to completed
        update_vegetable_status(doc_id, "completed", research_result)
        
        # Update Edge Agent Configuration -> DISABLED per user request (manual selection only)
        # update_edge_agent_config(research_result)
        
        logging.info(f"[Background] Research completed for {vegetable_name}")
        
    except Exception as e:
        logging.error(f"[Background] Research failed for {vegetable_name}: {e}")
        update_vegetable_status(doc_id, "failed", {"error": str(e)})

@app.post("/api/register-seed")
async def register_seed(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Receives image, starts async research, returns ID immediately.
    Used by Research Agent Dashboard.
    """
    try:
        # Read image
        content = await file.read()
        
        # 1. Analyze Seed Packet
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

@app.post("/api/vegetables/{doc_id}/select")
async def select_vegetable_endpoint(doc_id: str):
    """
    Selects the specified vegetable's research result as the active instruction for the Edge Agent.
    """
    try:
        # Import here to ensure it uses the latest db.py
        # Note: In production better to fix circular imports or structure, but this works for now given usage
        from backend.db import select_vegetable_instruction as select_func
    except ImportError:
        from db import select_vegetable_instruction as select_func

    success = select_func(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Failed to select vegetable (not found or no instruction).")
    
    return {"status": "success", "message": f"Edge Agent updated with instructions from {doc_id}"}

@app.get("/api/vegetables")
async def list_vegetables():
    """Returns list of all vegetables with current status."""
    return get_all_vegetables()

@app.get("/api/plant-camera/latest")
async def get_latest_plant_image():
    try:
        storage_client = storage.Client()
        bucket_name = "ai-agentic-hackathon-4-bk"
        bucket = storage_client.bucket(bucket_name)
        prefix = "logger-captures/"
        blobs = list(bucket.list_blobs(prefix=prefix))

        if not blobs:
            return {"error": "No images found"}
        
        image_blobs = [b for b in blobs if not b.name.endswith('/')]
        if not image_blobs:
            return {"error": "No image files found"}

        latest_blob = max(image_blobs, key=lambda b: b.time_created)
        image_data = latest_blob.download_as_bytes()
        b64_image = base64.b64encode(image_data).decode('utf-8')
        content_type = latest_blob.content_type or "image/jpeg"
        
        return {
            "image": f"data:{content_type};base64,{b64_image}",
            "timestamp": latest_blob.time_created.isoformat()
        }
    except Exception as e:
        import traceback
        logging.error(f"Error serving plant image: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# --- feature/#5 Endpoints (Async Firestore Jobs) ---

async def process_seed_guide(doc_id: str, image_bytes: bytes):
    """Background task to process seed guide generation."""
    
    # Import locally to ensure access to latest db functions if needed
    try:
        from backend.db import update_seed_guide_status as update_func
    except ImportError:
        from db import update_seed_guide_status as update_func

    # Update status to PROCESSING
    update_func(doc_id, "PROCESSING", "Starting analysis...")
    
    async def progress_callback(msg: str):
        print(f"[Guide {doc_id}] {msg}")
        update_func(doc_id, "PROCESSING", msg)

    try:
        # Check if analyze_seed_and_generate_guide is available
        if 'analyze_seed_and_generate_guide' in globals():
            steps = await analyze_seed_and_generate_guide(image_bytes, progress_callback)
            
            # Determine title from first step or default
            title = steps[0]['title'].split(' ')[0] + " Growing Guide" if steps else "Generated Guide"
            if "name" in steps[0]: title = steps[0]["name"] # if available
            
            # Update to COMPLETED with result using DB function
            # We need to construct the full object to save/update properly? 
            # actually update_seed_guide_status handles merging steps.
            # But we might want to set the title too. 
            # For now, update_seed_guide_status primarily handles status/message/steps.
            # Let's use save_seed_guide to update other metadata if needed, 
            # but update_seed_guide_status is enough for the "result".
            
            update_func(doc_id, "COMPLETED", "Complete!", steps)
            
            # Also update title if still default? 
            # For simplicity, we rely on the client or subsequent updates for title refinement 
            # OR we could update the doc directly here.
            # Let's keep it simple.
            
        else:
             update_func(doc_id, "FAILED", "Analysis service not available")

    except Exception as e:
        import traceback
        traceback.print_exc()
        update_func(doc_id, "FAILED", str(e))

@app.post("/api/seed-guide/generate")
async def generate_seed_guide_endpoint(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Starts an async seed guide generation, persisting immediately to Saved Guides."""
    try:
        content = await file.read()
        
        # Prepare initial data
        image_b64 = base64.b64encode(content).decode('utf-8')
        initial_data = {
            "title": "New Seed Guide", # Placeholder, updated later?
            "status": "PENDING",
            "message": "Queued for analysis...",
            "original_image": image_b64,
            "steps": []
        }
        
        # Create persistent document immediately
        try:
            from backend.db import save_seed_guide as save_func
        except ImportError:
            from db import save_seed_guide as save_func
            
        doc_id = save_func(initial_data)
        
        # Start background task
        background_tasks.add_task(process_seed_guide, doc_id, content)
        
        return {"job_id": doc_id, "status": "PENDING"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start generation: {str(e)}")

# Legacy job endpoints removed/deprecated in favor of unified flow

@app.get("/api/seed-guide/jobs/{job_id}")
async def get_seed_guide_job(job_id: str):
    """Polls the status of a seed guide job from Firestore."""
    try:
        doc_ref = db.collection(COLLECTION_NAME).document(job_id)
        doc = await doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Job not found")
            
        return doc.to_dict()
    except HTTPException:
        raise
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

class SaveGuideRequest(BaseModel):
    title: str
    description: Optional[str] = None
    steps: list
    original_image: Optional[str] = None # Base64 string of the original image

@app.post("/api/seed-guide/save")
async def save_seed_guide_endpoint(request: SaveGuideRequest):
    """Saves a generated seed guide."""
    try:
        # Import here to ensure it uses the latest db.py
        try:
            from backend.db import save_seed_guide as save_func
        except ImportError:
            from db import save_seed_guide as save_func
            
        doc_id = save_func(request.dict())
        return {"status": "success", "id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save guide: {str(e)}")

@app.get("/api/seed-guide/saved")
async def list_saved_guides():
    """Returns a list of saved seed guides."""
    try:
        try:
            from backend.db import get_all_seed_guides as list_func
        except ImportError:
            from db import get_all_seed_guides as list_func
            
        return list_func()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list guides: {str(e)}")

@app.get("/api/seed-guide/saved/{doc_id}")
async def get_saved_guide(doc_id: str):
    """Returns a specific saved seed guide."""
    try:
        try:
            from backend.db import get_seed_guide as get_func
        except ImportError:
            from db import get_seed_guide as get_func
            
        data = get_func(doc_id)
        if not data:
            raise HTTPException(status_code=404, detail="Guide not found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get guide: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
