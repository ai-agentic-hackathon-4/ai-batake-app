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

# Imports from HEAD (Legacy/Sync)
try:
    from .db import save_growing_instructions, get_latest_vegetable, get_sensor_history, get_recent_sensor_logs
    from .research_agent import analyze_seed_packet, perform_deep_research
    from .agent import get_weather_from_agent
except ImportError:
    # When running directly as a script
    from db import save_growing_instructions, get_latest_vegetable, get_sensor_history, get_recent_sensor_logs
    from research_agent import analyze_seed_packet, perform_deep_research
    from agent import get_weather_from_agent

# Imports from feature/#5 (Async/New)
# Assuming these modules exist in the codebase provided by feature/#5 merge
try:
    from .seed_service import analyze_seed_and_generate_guide
except ImportError:
    # Fallback or placeholder if missing
    pass

app = FastAPI()

# CORS config (HEAD)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Firestore Client (Async) from feature/#5
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
# Initialize AsyncClient if strictly needed for async features, 
# but be careful of event loop issues if mixing sync/async.
# For now, we initialize it globally.
db = firestore.AsyncClient(project=project_id)
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

# --- HEAD Endpoints (Sync/Legacy) ---

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

@app.post("/api/register-seed")
async def register_seed(file: UploadFile = File(...)):
    """
    Legacy synchronous endpoint used by current Next.js frontend.
    """
    try:
        content = await file.read()
        logging.info("Analyzing seed packet image...")
        packet_analysis_json = analyze_seed_packet(content)
        
        try:
            clean_text = packet_analysis_json.replace("```json", "").replace("```", "")
            analysis_data = json.loads(clean_text)
            vegetable_name = analysis_data.get("name", "Unknown Vegetable")
        except:
            vegetable_name = "Unknown Vegetable"
            analysis_data = {"raw": packet_analysis_json}
            
        logging.info(f"Identified vegetable: {vegetable_name}")
        logging.info(f"Performing deep research for: {vegetable_name}")
        research_result = perform_deep_research(vegetable_name, str(analysis_data))
        
        doc_id = save_growing_instructions(vegetable_name, research_result)
        
        return {
            "status": "success",
            "vegetable": vegetable_name,
            "document_id": doc_id,
            "research_data": research_result
        }
    except Exception as e:
        logging.error(f"Error in register_seed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

# --- feature/#5 Endpoints (Async) ---

async def process_seed_guide(job_id: str, image_bytes: bytes):
    """Background task to process seed guide generation."""
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
