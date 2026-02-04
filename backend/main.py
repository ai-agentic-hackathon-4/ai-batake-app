from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
import os
import base64
import json
from google.cloud import storage
from google.cloud import firestore
from dotenv import load_dotenv

# Import our structured logging module
try:
    from .logger import (
        get_logger, setup_logger, 
        generate_session_id, generate_request_id,
        set_session_id, set_request_id, get_session_id, get_request_id,
        info, debug, warning, error
    )
except ImportError:
    from logger import (
        get_logger, setup_logger,
        generate_session_id, generate_request_id,
        set_session_id, set_request_id, get_session_id, get_request_id,
        info, debug, warning, error
    )

# Setup structured logging
import logging
log_level = logging.DEBUG if os.environ.get("LOG_LEVEL", "DEBUG").upper() == "DEBUG" else logging.INFO
logger = setup_logger(level=log_level)

load_dotenv()

# Imports
try:
    # Try importing from feature/#3 db functions
    from .db import init_vegetable_status, update_vegetable_status, get_all_vegetables, update_edge_agent_config, get_latest_vegetable, get_sensor_history, get_recent_sensor_logs, get_agent_execution_logs
    # Also old ones just in case
    from .db import save_growing_instructions 
    from .research_agent import analyze_seed_packet, perform_deep_research
    from .agent import get_weather_from_agent
except ImportError:
    # When running directly as a script
    from db import init_vegetable_status, update_vegetable_status, get_all_vegetables, update_edge_agent_config, get_latest_vegetable, get_sensor_history, get_recent_sensor_logs, save_growing_instructions, get_agent_execution_logs
    from research_agent import analyze_seed_packet, perform_deep_research
    from agent import get_weather_from_agent

# Imports from feature/#5 (Async/New)
try:
    from .seed_service import analyze_seed_and_generate_guide
except ImportError:
    try:
        from seed_service import analyze_seed_and_generate_guide
    except ImportError as e:
        warning(f"Failed to import seed_service: {e}")
        pass

app = FastAPI()


class SessionTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add session and request ID tracking to each request.
    This enables tracing logs across the entire request lifecycle.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate or extract session ID
        # Check if client provided a session ID in headers
        session_id = request.headers.get("X-Session-ID") or generate_session_id()
        request_id = generate_request_id()
        
        # Set context variables for logging
        set_session_id(session_id)
        set_request_id(request_id)
        
        # Log request details
        method = request.method
        path = request.url.path
        query = str(request.query_params) if request.query_params else ""
        
        info(f"REQUEST START: {method} {path}" + (f"?{query}" if query else ""))
        # Filter out sensitive headers before logging
        safe_headers = {k: v for k, v in request.headers.items() 
                       if k.lower() not in ('authorization', 'cookie', 'x-api-key', 'api-key')}
        debug(f"Request headers: {safe_headers}")
        
        import time
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            elapsed_ms = (time.time() - start_time) * 1000
            info(f"REQUEST END: {method} {path} -> {response.status_code} ({elapsed_ms:.2f}ms)")
            
            # Add session/request IDs to response headers for client tracking
            response.headers["X-Session-ID"] = session_id
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            error(f"REQUEST ERROR: {method} {path} -> Exception ({elapsed_ms:.2f}ms): {str(e)}", exc_info=True)
            raise


# Add middlewares
app.add_middleware(SessionTrackingMiddleware)
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
        debug(f"Weather request for region: {request.region}")
        weather_info = get_weather_from_agent(request.region)
        info(f"Weather response received for {request.region}")
        return {"message": weather_info}
    except Exception as e:
        error(f"Weather request failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sensors/latest")
async def get_latest_sensor_log_endpoint():
    try:
        debug("Fetching latest sensor log")
        logs = get_recent_sensor_logs(limit=1)
        if logs and len(logs) > 0:
            debug(f"Sensor log found: temp={logs[0].get('temperature')}, humidity={logs[0].get('humidity')}")
            return logs[0]
        debug("No sensor logs found")
        return {}
    except Exception as e:
        error(f"Failed to fetch sensor logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sensor-history")
async def get_sensor_history_endpoint(hours: int = 24):
    try:
        debug(f"Fetching sensor history for {hours} hours")
        data = get_sensor_history(hours=hours)
        info(f"Sensor history retrieved: {len(data)} records")
        return {"data": data}
    except Exception as e:
        error(f"Failed to fetch sensor history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vegetables/latest")
async def get_latest_vegetable_endpoint():
    try:
        debug("Fetching latest vegetable")
        data = get_latest_vegetable()
        if data:
            info(f"Latest vegetable found: {data.get('name')}")
            return data
        else:
            debug("No vegetables found")
            return {} 

    except Exception as e:
        error(f"Failed to fetch latest vegetable: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agent-logs")
async def get_agent_logs_endpoint():
    try:
        debug("Fetching agent execution logs")
        logs = get_agent_execution_logs(limit=20)
        info(f"Agent logs retrieved: {len(logs)} entries")
        return {"logs": logs}
    except Exception as e:
        error(f"Failed to fetch agent logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# --- feature/#3 Endpoints (Research Agent UI Support) ---

def process_research(doc_id: str, vegetable_name: str, analysis_data: dict):
    """
    Background task to perform heavy deep research and update DB.
    """
    # Set a session ID for background task tracing
    task_session_id = f"bg-{doc_id[:8]}"
    set_session_id(task_session_id)
    set_request_id(generate_request_id())
    
    info(f"[Background] Starting research for {vegetable_name} (ID: {doc_id})")
    try:
        # Perform Deep Research
        debug(f"Calling perform_deep_research for {vegetable_name}")
        research_result = perform_deep_research(vegetable_name, str(analysis_data))
        
        # Merge analysis data (like original instructions) if needed
        if isinstance(research_result, dict):
            research_result["original_analysis"] = analysis_data
        
        # Update DB to completed
        debug(f"Updating vegetable status to completed for {doc_id}")
        update_vegetable_status(doc_id, "completed", research_result)
        
        # Update Edge Agent Configuration -> DISABLED per user request (manual selection only)
        # update_edge_agent_config(research_result)
        
        info(f"[Background] Research completed for {vegetable_name}")
        
    except Exception as e:
        error(f"[Background] Research failed for {vegetable_name}: {e}", exc_info=True)
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
        info(f"Received seed image: {file.filename}, size: {len(content)} bytes")
        
        # 1. Analyze Seed Packet
        info("Analyzing seed packet image...")
        packet_analysis_json = analyze_seed_packet(content)
        debug(f"Seed packet analysis result: {packet_analysis_json[:200]}...")
        
        # Parse analysis result
        try:
            clean_text = packet_analysis_json.replace("```json", "").replace("```", "")
            analysis_data = json.loads(clean_text)
            vegetable_name = analysis_data.get("name", "Unknown Vegetable")
        except:
            vegetable_name = "Unknown Vegetable"
            analysis_data = {"raw": packet_analysis_json}
            warning(f"Failed to parse analysis JSON, using raw format")
            
        info(f"Identified vegetable: {vegetable_name}")
        
        # 2. Initialize DB Document (Status: processing)
        doc_id = init_vegetable_status(vegetable_name)
        debug(f"Created document with ID: {doc_id}")
        
        # 3. Queue Background Task
        background_tasks.add_task(process_research, doc_id, vegetable_name, analysis_data)
        info(f"Background research task queued for {vegetable_name} (doc_id: {doc_id})")
        
        return {
            "status": "accepted",
            "message": "Research started in background",
            "document_id": doc_id,
            "vegetable": vegetable_name,
            "initial_analysis": analysis_data
        }
        
    except Exception as e:
        error(f"Error in register_seed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vegetables/{doc_id}/select")
async def select_vegetable_endpoint(doc_id: str):
    """
    Selects the specified vegetable's research result as the active instruction for the Edge Agent.
    """
    info(f"Selecting vegetable {doc_id} for edge agent")
    try:
        # Import here to ensure it uses the latest db.py
        # Note: In production better to fix circular imports or structure, but this works for now given usage
        from backend.db import select_vegetable_instruction as select_func
    except ImportError:
        from db import select_vegetable_instruction as select_func

    success = select_func(doc_id)
    if not success:
        warning(f"Failed to select vegetable {doc_id} - not found or no instruction")
        raise HTTPException(status_code=404, detail="Failed to select vegetable (not found or no instruction).")
    
    info(f"Successfully selected vegetable {doc_id} for edge agent")
    return {"status": "success", "message": f"Edge Agent updated with instructions from {doc_id}"}

@app.get("/api/vegetables")
async def list_vegetables():
    """Returns list of all vegetables with current status."""
    debug("Fetching all vegetables")
    result = get_all_vegetables()
    info(f"Retrieved {len(result)} vegetables")
    return result

@app.get("/api/plant-camera/latest")
async def get_latest_plant_image():
    try:
        debug("Fetching latest plant camera image")
        storage_client = storage.Client()
        bucket_name = "ai-agentic-hackathon-4-bk"
        bucket = storage_client.bucket(bucket_name)
        prefix = "logger-captures/"
        blobs = list(bucket.list_blobs(prefix=prefix))

        if not blobs:
            warning("No plant images found in storage")
            return {"error": "No images found"}
        
        image_blobs = [b for b in blobs if not b.name.endswith('/')]
        if not image_blobs:
            warning("No image files found in plant camera folder")
            return {"error": "No image files found"}

        latest_blob = max(image_blobs, key=lambda b: b.time_created)
        info(f"Serving plant image: {latest_blob.name}")
        image_data = latest_blob.download_as_bytes()
        b64_image = base64.b64encode(image_data).decode('utf-8')
        content_type = latest_blob.content_type or "image/jpeg"
        
        return {
            "image": f"data:{content_type};base64,{b64_image}",
            "timestamp": latest_blob.time_created.isoformat()
        }
    except Exception as e:
        import traceback
        error(f"Error serving plant image: {traceback.format_exc()}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# --- feature/#5 Endpoints (Async Firestore Jobs) ---

async def process_seed_guide(job_id: str, image_bytes: bytes):
    """Background task to process seed guide generation (Feature #5)."""
    # Set session ID for background task tracing
    task_session_id = f"job-{job_id[:8]}"
    set_session_id(task_session_id)
    set_request_id(generate_request_id())
    
    info(f"Starting seed guide generation job: {job_id}")
    doc_ref = db.collection(COLLECTION_NAME).document(job_id)
    
    await doc_ref.update({
        "status": "PROCESSING",
        "message": "Starting analysis..."
    })
    
    async def progress_callback(msg: str):
        debug(f"[Job {job_id}] Progress: {msg}")
        await doc_ref.update({"message": msg})

    try:
        # Check if analyze_seed_and_generate_guide is available
        if 'analyze_seed_and_generate_guide' in globals():
            debug(f"Calling analyze_seed_and_generate_guide for job {job_id}")
            steps = await analyze_seed_and_generate_guide(image_bytes, progress_callback)
            info(f"Seed guide job {job_id} completed with {len(steps)} steps")
            await doc_ref.update({
                "status": "COMPLETED",
                "result": steps,
                "message": "Complete!"
            })
        else:
            warning(f"analyze_seed_and_generate_guide not available for job {job_id}")
            await doc_ref.update({
                "status": "FAILED",
                "message": "Analysis service not available"
            })
    except Exception as e:
        import traceback
        error(f"Seed guide job {job_id} failed: {str(e)}", exc_info=True)
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
        
        info(f"Creating seed guide job: {job_id}, file: {file.filename}, size: {len(content)} bytes")
        
        doc_ref = db.collection(COLLECTION_NAME).document(job_id)
        await doc_ref.set({
            "job_id": job_id,
            "status": "PENDING",
            "message": "Job created, waiting for worker...",
            "result": None,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        
        background_tasks.add_task(process_seed_guide, job_id, content)
        debug(f"Background task queued for job {job_id}")
        
        return {"job_id": job_id}
    except Exception as e:
        error(f"Failed to create seed guide job: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start job: {str(e)}")

@app.get("/api/seed-guide/jobs/{job_id}")
async def get_seed_guide_job(job_id: str):
    """Polls the status of a seed guide job from Firestore."""
    try:
        debug(f"Fetching job status: {job_id}")
        doc_ref = db.collection(COLLECTION_NAME).document(job_id)
        doc = await doc_ref.get()
        
        if not doc.exists:
            warning(f"Job not found: {job_id}")
            raise HTTPException(status_code=404, detail="Job not found")
        
        job_data = doc.to_dict()
        debug(f"Job {job_id} status: {job_data.get('status')}")
        return job_data
    except HTTPException:
        raise
    except Exception as e:
        error(f"Failed to fetch job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    startup_session = generate_session_id()
    set_session_id(startup_session)
    set_request_id("startup")
    info("AI Batake Backend started successfully")
    info(f"Project ID: {project_id}")
    debug(f"Firestore collection: {COLLECTION_NAME}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
