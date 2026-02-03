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
    from .db import init_vegetable_status, update_vegetable_status, get_all_vegetables, update_edge_agent_config, get_latest_vegetable, get_sensor_history, get_recent_sensor_logs
    # Also old ones just in case
    from .db import save_growing_instructions 
    from .research_agent import analyze_seed_packet, perform_deep_research
    from .agent import get_weather_from_agent
except ImportError:
    # When running directly as a script
    from db import init_vegetable_status, update_vegetable_status, get_all_vegetables, update_edge_agent_config, get_latest_vegetable, get_sensor_history, get_recent_sensor_logs, save_growing_instructions
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

async def process_seed_guide(job_id: str, image_bytes: bytes):
    """Background task to process seed guide generation (Feature #5)."""
    doc_ref = db.collection(COLLECTION_NAME).document(job_id)
    
    await doc_ref.update({
        "status": "PROCESSING",
        "message": "Starting analysis..."
    })
    
    async def progress_callback(msg: str):
        print(f"[Job {job_id}] {msg}")
        await doc_ref.update({"message": msg})

    try:
        # Check if analyze_seed_and_generate_guide is available
        if 'analyze_seed_and_generate_guide' in globals():
            steps = await analyze_seed_and_generate_guide(image_bytes, progress_callback)
            await doc_ref.update({
                "status": "COMPLETED",
                "result": steps,
                "message": "Complete!"
            })
        else:
             await doc_ref.update({
                "status": "FAILED",
                "message": "Analysis service not available"
            })
    except Exception as e:
        import traceback
        traceback.print_exc()
        await doc_ref.update({
            "status": "FAILED",
            "message": str(e)
        })

@app.post("/api/seed-guide/jobs")
async def create_seed_guide_job(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Starts an async job using feature/#5 architecture."""
    try:
        content = await file.read()
        job_id = str(uuid.uuid4())
        
        doc_ref = db.collection(COLLECTION_NAME).document(job_id)
        await doc_ref.set({
            "job_id": job_id,
            "status": "PENDING",
            "message": "Job created, waiting for worker...",
            "result": None,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        
        background_tasks.add_task(process_seed_guide, job_id, content)
        
        return {"job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start job: {str(e)}")

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
