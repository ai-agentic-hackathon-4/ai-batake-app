from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
import os
import time
import base64
import json
import asyncio
from datetime import datetime
from google.cloud import storage
from google.cloud import firestore
from dotenv import load_dotenv

# Import our structured logging module
try:
    from .logger import (
        setup_logger,
        generate_session_id, generate_request_id,
        set_session_id, set_request_id,
        info, debug, warning, error
    )
except ImportError:
    from logger import (
        setup_logger,
        generate_session_id, generate_request_id,
        set_session_id, set_request_id,
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
    from .db import (
        init_vegetable_status, update_vegetable_status, 
        get_all_vegetables, get_latest_vegetable, 
        get_sensor_history, get_recent_sensor_logs, get_agent_execution_logs,
        get_all_seed_guides, save_seed_guide, get_seed_guide
    )
    from .research_agent import analyze_seed_packet, perform_deep_research, perform_web_grounding_research
    from .agent import get_weather_from_agent
except ImportError:
    # When running directly as a script
    from db import (
        init_vegetable_status, update_vegetable_status, 
        get_all_vegetables, get_latest_vegetable, 
        get_sensor_history, get_recent_sensor_logs, get_agent_execution_logs,
        get_all_seed_guides, save_seed_guide, get_seed_guide
    )
    from research_agent import analyze_seed_packet, perform_deep_research, perform_web_grounding_research
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

# Imports for Character Service
try:
    from .character_service import analyze_seed_and_generate_character
except ImportError:
    try:
        from character_service import analyze_seed_and_generate_character
    except ImportError:
        pass

# Imports for Diary Service
try:
    from .diary_service import (
        process_daily_diary,
        get_all_diaries,
        get_diary_by_date
    )
except ImportError:
    try:
        from diary_service import (
            process_daily_diary,
            get_all_diaries,
            get_diary_by_date
        )
    except ImportError as e:
        warning(f"Failed to import diary_service: {e}")
        process_daily_diary = None
        get_all_diaries = None
        get_diary_by_date = None

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
        debug(f"Weather response received for {request.region}")
        return {"message": weather_info}
    except Exception as e:
        error(f"Weather request failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sensors/latest")
async def get_latest_sensor_log_endpoint():
    try:
        debug("Fetching latest sensor log")
        logs = await asyncio.to_thread(get_recent_sensor_logs, limit=1)
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
        data = await asyncio.to_thread(get_sensor_history, hours=hours)
        info(f"Sensor history retrieved: {len(data)} records")
        return {"data": data}
    except Exception as e:
        error(f"Failed to fetch sensor history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vegetables/latest")
async def get_latest_vegetable_endpoint():
    try:
        debug("Fetching latest vegetable")
        data = await asyncio.to_thread(get_latest_vegetable)
        if data:
            debug(f"Latest vegetable found: {data.get('name')}")
            return data
        else:
            debug("No vegetables found")
            return {} 

    except Exception as e:
        error(f"Failed to fetch latest vegetable: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agent-logs/oldest")
async def get_oldest_agent_log_endpoint():
    """Get the oldest agent log to calculate days since planting"""
    try:
        debug("Fetching oldest agent execution log")
        collection_name = "agent_execution_logs"
        
        # Using the global async db client
        from google.cloud import firestore as fs
        query = db.collection(collection_name).order_by("timestamp", direction=fs.Query.ASCENDING).limit(1)
        docs = await query.get()
        
        if docs:
            oldest_log = docs[0].to_dict()
            info(f"Oldest log timestamp: {oldest_log.get('timestamp')}")
            return {"timestamp": oldest_log.get("timestamp")}
        else:
            warning("No agent logs found")
            return {"timestamp": None}
    except Exception as e:
        error(f"Failed to fetch oldest agent log: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent-logs")
async def get_agent_logs_endpoint():
    try:
        debug("Fetching agent execution logs")
        logs = await asyncio.to_thread(get_agent_execution_logs, limit=20)
        info(f"Agent logs retrieved: {len(logs)} entries")
        return {"logs": logs}
    except Exception as e:
        error(f"Failed to fetch agent logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# --- feature/#3 Endpoints (Research Agent UI Support) ---

def process_research(doc_id: str, vegetable_name: str, analysis_data: dict, mode: str = "agent"):
    """
    Background task to perform heavy research and update DB.
    mode: "agent" (Deep Research Agent) or "grounding" (Google Search Grounding)
    """
    # Set a session ID for background task tracing
    task_session_id = f"bg-{doc_id[:8]}"
    set_session_id(task_session_id)
    set_request_id(generate_request_id())
    
    info(f"[Background] Starting research for {vegetable_name} (ID: {doc_id}, mode: {mode})")
    try:
        # Perform Research based on mode
        if mode == "grounding":
            info(f"[LLM] Calling Web Grounding research for {vegetable_name}")
            research_result = perform_web_grounding_research(vegetable_name, str(analysis_data))
        else:
            info(f"[LLM] Calling Deep Research for {vegetable_name}")
            research_result = perform_deep_research(vegetable_name, str(analysis_data))
        
        # Merge analysis data (like original instructions) if needed
        if isinstance(research_result, dict):
            research_result["original_analysis"] = analysis_data
        
        # Update DB to completed (UPPERCASE for frontend compatibility)
        info(f"Updating vegetable status to COMPLETED for {doc_id}")
        update_vegetable_status(doc_id, "COMPLETED", research_result)
        
        # Update Edge Agent Configuration -> DISABLED per user request (manual selection only)
        # update_edge_agent_config(research_result)
        
        info(f"[Background] Research completed for {vegetable_name}")
        
    except Exception as e:
        error(f"[Background] Research failed for {vegetable_name}: {e}", exc_info=True)
        update_vegetable_status(doc_id, "failed", {"error": str(e)})

@app.post("/api/register-seed")
async def register_seed(background_tasks: BackgroundTasks, file: UploadFile = File(...), research_mode: str = "agent"):
    """
    Receives image, starts async research, returns ID immediately.
    Used by Research Agent Dashboard.
    """
    try:
        # Read image
        content = await file.read()
        info(f"Received seed image: {file.filename}, size: {len(content)} bytes")
        
        # 1. Analyze Seed Packet
        info("[LLM] 📸 Analyzing seed packet image...")
        packet_analysis_json = analyze_seed_packet(content)
        info(f"[LLM] ✅ Seed packet analysis completed ({len(packet_analysis_json)} chars)")
        
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
        info(f"Created document with ID: {doc_id}")
        
        # 3. Queue Background Task
        background_tasks.add_task(process_research, doc_id, vegetable_name, analysis_data, mode=research_mode)
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
    debug(f"Retrieved {len(result)} vegetables")
    return result

@app.delete("/api/vegetables/{doc_id}")
async def delete_vegetable(doc_id: str):
    """Deletes a vegetable research document."""
    try:
        await db.collection("vegetables").document(doc_id).delete()
        info(f"Deleted vegetable doc: {doc_id}")
        return {"status": "success", "id": doc_id}
    except Exception as e:
        error(f"Failed to delete vegetable {doc_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/plant-camera/latest")
async def get_latest_plant_image():
    try:
        debug("Fetching latest plant camera image")
        
        # Move blocking GCS operations to a thread
        def _get_image_data():
            storage_client = storage.Client()
            bucket_name = "ai-agentic-hackathon-4-bk"
            bucket = storage_client.bucket(bucket_name)
            prefix = "logger-captures/"
            blobs = list(bucket.list_blobs(prefix=prefix))

            if not blobs:
                return None, "No images found"
            
            image_blobs = [b for b in blobs if not b.name.endswith('/')]
            if not image_blobs:
                return None, "No image files found"

            latest_blob = max(image_blobs, key=lambda b: b.time_created)
            info(f"Serving plant image: {latest_blob.name}")
            data = latest_blob.download_as_bytes()
            return {
                "content": data,
                "content_type": latest_blob.content_type or "image/jpeg",
                "timestamp": latest_blob.time_created.isoformat()
            }, None

        result, error_msg = await asyncio.to_thread(_get_image_data)
        
        if error_msg:
            warning(error_msg)
            return {"error": error_msg}

        # Base64 encoding can also be blocking for large data (1.8MB)
        def _encode_base64(data, content_type):
            b64 = base64.b64encode(data).decode('utf-8')
            return f"data:{content_type};base64,{b64}"

        b64_image = await asyncio.to_thread(_encode_base64, result["content"], result["content_type"])
        
        return {
            "image": b64_image,
            "timestamp": result["timestamp"]
        }
    except Exception as e:
        error(f"Error serving plant image: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def _download_from_gcs_sync(bucket_name, blob_name):
    """Sync helper to download bytes from GCS."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.download_as_bytes()

def _upload_to_gcs_sync(bucket_name, blob_name, content, content_type):
    """Sync helper to upload bytes/string to GCS."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    if isinstance(content, str):
        blob.upload_from_string(content, content_type=content_type)
    else:
        blob.upload_from_string(content, content_type=content_type)
    return f"https://storage.googleapis.com/{bucket_name}/{blob_name}"

# --- feature/#5 Endpoints (Async Firestore Jobs) ---

async def process_seed_guide(job_id: str, image_source: str, image_model: str = "pro", guide_image_mode: str = "single"):
    """Background task to process seed guide generation (Feature #5)."""
    # Set session ID for background task tracing
    task_session_id = f"job-{job_id[:8]}"
    set_session_id(task_session_id)
    set_request_id(generate_request_id())
    
    info(f"[SeedGuide] start job={job_id}")
    doc_ref = db.collection(COLLECTION_NAME).document(job_id)
    
    await doc_ref.set({
        "status": "PROCESSING",
        "message": "Starting analysis..."
    }, merge=True)
    
    async def progress_callback(msg: str):
        info(f"[Job {job_id}] Progress: {msg}")
        await doc_ref.set({"message": msg}, merge=True)

    # Download image if source is a path/URL
    image_bytes = None
    try:
        bucket_name = "ai-agentic-hackathon-4-bk"
        blob_name = None
        
        if isinstance(image_source, str) and image_source.startswith("gs://"):
            blob_name = image_source.replace(f"gs://{bucket_name}/", "")
        elif isinstance(image_source, bytes):
            image_bytes = image_source
        else:
            # Fallback: assume it is a blob name if string
            blob_name = image_source
            
        if blob_name:
            info(f"Downloading input image from GCS: {blob_name}")
            image_bytes = await asyncio.to_thread(_download_from_gcs_sync, bucket_name, blob_name)
             
    except Exception as e:
        error(f"Failed to download input image: {e}")
        await doc_ref.set({"status": "FAILED", "message": "Failed to retrieve input image"}, merge=True)
        return

    try:
        # Check if analyze_seed_and_generate_guide is available
        if 'analyze_seed_and_generate_guide' in globals():
            info(f"[SeedGuide][LLM] analyze start job={job_id}")
            analyze_start_ts = time.time()
            
            # Unpack the new return values (title, description, steps)
            guide_title, guide_description, steps = await analyze_seed_and_generate_guide(image_bytes, progress_callback, image_model=image_model, guide_image_mode=guide_image_mode)
            analyze_elapsed_ms = (time.time() - analyze_start_ts) * 1000
            info(f"[SeedGuide][LLM] analyze done job={job_id} ms={analyze_elapsed_ms:.0f}")
            
            # Post-process steps: Upload generated images to GCS
            info(f"[SeedGuide] upload_images job={job_id} count={len(steps)}")
            
            for i, step in enumerate(steps):
                if step.get("image_base64"):
                    try:
                        b64_data = step["image_base64"]
                        img_data = base64.b64decode(b64_data)
                        timestamp = int(time.time())
                        blob_name = f"seed-guides/output/{job_id}_{timestamp}_{i}.jpg"
                        
                        image_url = await asyncio.to_thread(
                            _upload_to_gcs_sync, 
                            "ai-agentic-hackathon-4-bk", 
                            blob_name, 
                            img_data, 
                            "image/jpeg"
                        )
                        
                        # Replace base64 with Proxy URL
                        step["image_url"] = f"/api/seed-guide/image/{job_id}/{i}"
                        if "image_base64" in step:
                            del step["image_base64"]
                    except Exception as img_e:
                        warning(f"Failed to upload output image {i}: {img_e}")
            info(f"[SeedGuide] completed job={job_id} steps={len(steps)}")
            
            # Update to COMPLETED with result using DB function or manual update
            update_data = {
                "status": "COMPLETED",
                "result": steps,
                "steps": steps, 
                "message": "Complete!"
            }
            
            # Only update title/description if they are valid
            if guide_title and guide_title != "Seed Guide":
                update_data["title"] = guide_title
            
            if guide_description:
                 update_data["description"] = guide_description
                 
            await doc_ref.set(update_data, merge=True)
        else:
            warning(f"[SeedGuide] analyze_unavailable job={job_id}")
            await doc_ref.set({
                "status": "FAILED",
                "message": "Analysis service not available"
            }, merge=True)
    except Exception as e:
        error(f"[SeedGuide] failed job={job_id} error={str(e)}", exc_info=True)
        await doc_ref.set({
            "status": "FAILED",
            "message": str(e)
        }, merge=True)

@app.post("/api/seed-guide/generate")
async def generate_seed_guide_endpoint(background_tasks: BackgroundTasks, file: UploadFile = File(...), image_model: str = "pro", guide_image_mode: str = "single"):
    """Starts an async seed guide generation, persisting immediately to Saved Guides."""
    try:
        # Upload to GCS (streaming)
        job_id = str(uuid.uuid4())
        info(f"Creating seed guide job: {job_id}, file: {file.filename}")
        
        bucket_name = "ai-agentic-hackathon-4-bk"
        try:
            timestamp = int(time.time())
            safe_filename = file.filename.replace(" ", "_").replace("/", "_")
            blob_name = f"seed-guides/input/{timestamp}_{safe_filename}"
            
            info(f"Uploading input image to GCS: {blob_name}")
            content = await file.read()
            
            # Use sync helper in thread
            image_url = await asyncio.to_thread(
                _upload_to_gcs_sync,
                bucket_name,
                blob_name,
                content,
                file.content_type
            )

        except Exception as e:
            error(f"Failed to upload input to GCS: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload image: {e}")

        # Create persistent document immediately
        doc_ref = db.collection(COLLECTION_NAME).document(job_id)
        
        await doc_ref.set({
            "job_id": job_id, 
            "title": "New Seed Guide",
            "status": "PENDING",
            "message": "Job created, waiting for worker...",
            "input_image_url": image_url,
            "result": None,
            "steps": [], 
            "created_at": firestore.SERVER_TIMESTAMP
        })
        
        # Pass blob_name (str) instead of content (bytes)
        background_tasks.add_task(process_seed_guide, job_id, blob_name, image_model=image_model, guide_image_mode=guide_image_mode)
        info(f"Background task queued for job {job_id}")

        return {"job_id": job_id, "status": "PENDING"}
        
    except Exception as e:
        error(f"Failed to start generation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start generation: {str(e)}")

# Legacy job endpoints removed/deprecated in favor of unified flow

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
        
        def make_serializable(obj):
            if isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(v) for v in obj]
            elif hasattr(obj, 'isoformat'):
                return obj.isoformat()
            elif isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            else:
                return str(obj)

        job_data = make_serializable(job_data)
        
        if "result" in job_data and isinstance(job_data["result"], dict):
            res = job_data["result"]
            if res.get("image_url") and res["image_url"].startswith("https://storage.googleapis.com/"):
                gcs_uri = res["image_url"]
                bucket_name = "ai-agentic-hackathon-4-bk"
                prefix = f"https://storage.googleapis.com/{bucket_name}/"
                
                if gcs_uri.startswith(prefix):
                    blob_path = gcs_uri[len(prefix):]
                    import urllib.parse
                    encoded_path = urllib.parse.quote(blob_path)
                    res["image_url"] = f"/api/character/image?path={encoded_path}"
                    # Ensure base64 is cleared if it exists (though backend job clears it usually)
                    if "image_base64" in res:
                        del res["image_base64"]

        info(f"Job {job_id} status: {job_data.get('status')}")
        return job_data
    except HTTPException:
        raise
    except Exception as e:
        error(f"Failed to fetch job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# --- Character Generation Endpoints ---

async def process_character_generation(job_id: str, image_bytes: bytes):
    """Background task to process character generation."""
    task_session_id = f"char-{job_id[:8]}"
    set_session_id(task_session_id)
    set_request_id(generate_request_id())
    
    info(f"[Character] start job={job_id}")
    doc_ref = db.collection("character_jobs").document(job_id)
    
    await doc_ref.update({
        "status": "PROCESSING",
        "message": "Generating character..."
    })
    
    try:
        # Check if analyze_seed_and_generate_character is available
        if 'analyze_seed_and_generate_character' in globals():
            info(f"[Character][LLM] analyze start job={job_id}")
            analyze_start_ts = time.time()
            result = await analyze_seed_and_generate_character(image_bytes)
            analyze_elapsed_ms = (time.time() - analyze_start_ts) * 1000
            info(f"[Character][LLM] analyze done job={job_id} ms={analyze_elapsed_ms:.0f}")
            
            # Save image to GCS
            if result.get("image_base64"):
                try:
                    b64_data = result["image_base64"]
                    img_data = base64.b64decode(b64_data)
                    timestamp = int(time.time())
                    blob_name = f"characters/{job_id}_{timestamp}.png"
                    
                    # Upload to GCS
                    info(f"[Character] upload_image job={job_id} blob={blob_name}")
                    image_url = await asyncio.to_thread(
                        _upload_to_gcs_sync, 
                        "ai-agentic-hackathon-4-bk", 
                        blob_name, 
                        img_data, 
                        "image/png"
                    )
                    
                    # Update result with URL
                    result["image_url"] = image_url
                    
                    info(
                        f"[Character] image uploaded job={job_id} url={image_url}"
                    )
                    
                    # Remove base64 from result to save space in job doc
                    del result["image_base64"]
                    
                except Exception as img_e:
                    warning(f"Failed to save character image/data: {img_e}")
                    # Continue to complete job even if saving failed? 
                    # Probably better to report error but let job complete with base64 if upload fails?
                    # For now, let's just log and continue, result still has base64 if del didn't happen
                    pass

            await doc_ref.update({
                "status": "COMPLETED",
                "result": result,
                "message": "Character generated!"
            })
        else:
            warning(f"[Character] analyze_unavailable job={job_id}")
            await doc_ref.update({
                "status": "FAILED",
                "message": "Analysis service not available"
            })
    except Exception as e:
        error(f"[Character] failed job={job_id} error={str(e)}", exc_info=True)
        await doc_ref.update({
            "status": "FAILED",
            "message": str(e)
        })

@app.get("/api/character/jobs/{job_id}")
async def get_character_job_status(job_id: str):
    """Polls the status of a character generation job from Firestore."""
    try:
        debug(f"Fetching character job status: {job_id}")
        doc_ref = db.collection("character_jobs").document(job_id)
        doc = await doc_ref.get()
        
        if not doc.exists:
            warning(f"Character job not found: {job_id}")
            raise HTTPException(status_code=404, detail="Job not found")
        
        job_data = doc.to_dict()
        
        def make_serializable(obj):
            if isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(v) for v in obj]
            elif hasattr(obj, 'isoformat'):
                return obj.isoformat()
            elif isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            else:
                return str(obj)

        job_data = make_serializable(job_data)
        
        # Proxy GCS image URL if present
        if "result" in job_data and isinstance(job_data["result"], dict):
            res = job_data["result"]
            if res.get("image_url") and res["image_url"].startswith("https://storage.googleapis.com/"):
                gcs_uri = res["image_url"]
                bucket_name = "ai-agentic-hackathon-4-bk"
                prefix = f"https://storage.googleapis.com/{bucket_name}/"
                
                if gcs_uri.startswith(prefix):
                    blob_path = gcs_uri[len(prefix):]
                    import urllib.parse
                    encoded_path = urllib.parse.quote(blob_path)
                    res["image_url"] = f"/api/character/image?path={encoded_path}"
                    if "image_base64" in res:
                        del res["image_base64"]

        info(f"Character job {job_id} status: {job_data.get('status')}")
        return job_data
    except HTTPException:
        raise
    except Exception as e:
        error(f"Failed to fetch character job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/character/list")
async def list_characters():
    """Returns a list of all completed character jobs."""
    try:
        from backend.db import get_all_character_jobs
    except ImportError:
        from db import get_all_character_jobs
        
    jobs = get_all_character_jobs()
    
    # Proxy URLs for all jobs
    for job in jobs:
        if "result" in job and isinstance(job["result"], dict):
            res = job["result"]
            if res.get("image_url") and res["image_url"].startswith("https://storage.googleapis.com/"):
                gcs_uri = res["image_url"]
                bucket_name = "ai-agentic-hackathon-4-bk"
                prefix = f"https://storage.googleapis.com/{bucket_name}/"
                
                if gcs_uri.startswith(prefix):
                    blob_path = gcs_uri[len(prefix):]
                    import urllib.parse
                    encoded_path = urllib.parse.quote(blob_path)
                    res["image_url"] = f"/api/character/image?path={encoded_path}"
                    
                    # Ensure compatibility with frontend expectations
                    if "image_uri" not in res:
                        res["image_uri"] = res["image_url"]
    
    return jobs

@app.post("/api/character/{job_id}/select")
async def select_character_endpoint(job_id: str):
    """Selects the specified character job results as the active character for the diary."""
    info(f"Selecting character {job_id} for diary")
    try:
        from backend.db import select_character_for_diary as select_func
    except ImportError:
        from db import select_character_for_diary as select_func

    success = select_func(job_id)
    if not success:
        warning(f"Failed to select character {job_id}")
        raise HTTPException(status_code=404, detail="Failed to select character (not found or not completed).")
    
    info(f"Successfully selected character {job_id}")
    return {"status": "success", "message": f"Diary character updated to {job_id}"}

@app.get("/api/character")
async def get_character():
    """
    Returns the current character from /growing_diaries/Character.
    The image_uri is transformed to a local proxy URL.
    """
    try:
        doc_ref = db.collection("growing_diaries").document("Character")
        doc = await doc_ref.get()
        
        if not doc.exists:
            return {}
        
        data = doc.to_dict()
        
        # Transform image_uri to proxy URL
        if data.get("image_uri") and data["image_uri"].startswith("https://storage.googleapis.com/"):
            # Extract path after bucket name or full path?
            # Let's just pass the full GCS path to the proxy for simplicity, or relative path
            # The proxy implementation below expects relative path after bucket
            gcs_uri = data["image_uri"]
            bucket_name = "ai-agentic-hackathon-4-bk"
            prefix = f"https://storage.googleapis.com/{bucket_name}/"
            
            if gcs_uri.startswith(prefix):
                blob_path = gcs_uri[len(prefix):]
                # Encode path to be safe in query param
                import urllib.parse
                encoded_path = urllib.parse.quote(blob_path)
                data["image_uri"] = f"/api/character/image?path={encoded_path}"
                
        return data
    except Exception as e:
        error(f"Failed to get character: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/character/image")
async def get_character_image(path: str):
    """
    Proxies character image from GCS.
    Path should be relative to bucket root.
    """
    try:
        bucket_name = "ai-agentic-hackathon-4-bk"
        
        # Security check: basic path traversal prevention
        if ".." in path or path.startswith("/"):
             raise HTTPException(status_code=400, detail="Invalid path")
             
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(path)
        
        if not blob.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        
        img_bytes = blob.download_as_bytes()
        from fastapi import Response
        return Response(content=img_bytes, media_type="image/png")
        
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error serving character image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/seed-guide/character")
async def create_character_job(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Starts an async job for character generation."""
    try:
        content = await file.read()
        job_id = str(uuid.uuid4())
        
        info(f"Creating character generation job: {job_id}, file: {file.filename}")
        
        doc_ref = db.collection("character_jobs").document(job_id)
        await doc_ref.set({
            "job_id": job_id,
            "status": "PENDING",
            "message": "Job created...",
            "result": None,
            "created_at": firestore.SERVER_TIMESTAMP,
            "type": "character" 
        })
        
        background_tasks.add_task(process_character_generation, job_id, content)
        
        return {"job_id": job_id}
    except Exception as e:
        error(f"Failed to create character job: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start job: {str(e)}")

class SaveGuideRequest(BaseModel):
    title: str
    description: Optional[str] = None
    steps: list

@app.post("/api/seed-guide/save")
async def save_seed_guide_endpoint(request: SaveGuideRequest):
    """Saves a generated seed guide."""
    try:
        # Use globally imported save_seed_guide
        doc_id = await asyncio.to_thread(save_seed_guide, request.dict())
        return {"status": "success", "id": doc_id}
    except Exception as e:
        error(f"Failed to save guide: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save guide: {str(e)}")

@app.get("/api/seed-guide/saved")
async def list_saved_guides():
    """Returns a list of saved seed guides."""
    try:
        # Use globally imported get_all_seed_guides
        return await asyncio.to_thread(get_all_seed_guides)
    except Exception as e:
        error(f"Failed to list guides: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list guides: {str(e)}")

def _hydrate_image_for_frontend(url: str):
    """Downloads image from GCS URL and returns base64 string (Sync)."""
    try:
        bucket_name = "ai-agentic-hackathon-4-bk"
        if url.startswith("https://storage.googleapis.com/"):
            # Extract relative path from URL
            prefix = f"https://storage.googleapis.com/{bucket_name}/"
            if url.startswith(prefix):
                 blob_name = url[len(prefix):]
                 storage_client = storage.Client()
                 bucket = storage_client.bucket(bucket_name)
                 blob = bucket.blob(blob_name)
                 image_data = blob.download_as_bytes()
                 return base64.b64encode(image_data).decode('utf-8')
        return None
    except Exception as e:
        warning(f"Failed to hydrate image from {url}: {e}")
        return None

@app.get("/api/seed-guide/saved/{doc_id}")
async def get_saved_guide(doc_id: str):
    """Returns a specific saved seed guide with hydrated images."""
    try:
        # Use globally imported get_seed_guide
        data = await asyncio.to_thread(get_seed_guide, doc_id)
        if not data:
            raise HTTPException(status_code=404, detail="Guide not found")
        
        # Hydrate images if needed
        if "steps" in data:
            debug(f"Hydrating images for guide {doc_id}...")
            async def hydrate_step(step):
                if step.get("image_url") and not step.get("image_base64"):
                     b64 = await asyncio.to_thread(_hydrate_image_for_frontend, step["image_url"])
                     if b64:
                         step["image_base64"] = b64
                         del step["image_url"]
            
            tasks = [hydrate_step(step) for step in data["steps"]]
            await asyncio.gather(*tasks)
            debug(f"Hydration complete for guide {doc_id}")

        return data
    except HTTPException:
        raise
    except Exception as e:
        error(f"Failed to get guide: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get guide: {str(e)}")

@app.delete("/api/seed-guide/saved/{doc_id}")
async def delete_saved_guide(doc_id: str):
    """Deletes a saved seed guide document."""
    try:
        await db.collection(COLLECTION_NAME).document(doc_id).delete()
        info(f"Deleted seed guide doc: {doc_id}")
        return {"status": "success", "id": doc_id}
    except Exception as e:
        error(f"Failed to delete guide {doc_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# --- Diary Endpoints ---

class DiaryGenerateRequest(BaseModel):
    date: str  # ISO format date string (YYYY-MM-DD)

class ProgressWrapper:
    def __init__(self):
        self.queue = asyncio.Queue()
    
    async def callback(self, msg):
        await self.queue.put(msg)
    
    async def __aiter__(self):
        while True:
            msg = await self.queue.get()
            if msg == "__DONE__":
                break
            yield msg

@app.post("/api/diary/auto-generate")
async def auto_generate_diary_endpoint(key: Optional[str] = None):
    """
    Endpoint for Cloud Scheduler to trigger automatic diary generation.
    Secured by a simple API key check.
    """
    secret_key = os.environ.get("DIARY_API_KEY")
    if secret_key and key != secret_key:
        error(f"Unauthorized attempt to trigger auto-generation (key: {key})")
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        current_date_str = datetime.now().date().isoformat()
        info(f"Auto-generating diary for today: {current_date_str}")
        
        asyncio.create_task(process_daily_diary(current_date_str))
        
        return {
            "status": "accepted",
            "date": current_date_str,
            "message": "Automatic diary generation started"
        }
    except Exception as e:
        error(f"Failed to trigger auto-generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/diary/generate-manual")
async def generate_manual_diary_endpoint(
    request: DiaryGenerateRequest
):
    """
    Trigger manual diary generation for a specific date and stream progress.
    """
    if process_daily_diary is None:
        raise HTTPException(status_code=503, detail="Diary service not available")
    
    try:
        from datetime import date as date_module
        
        try:
            target_date_obj = date_module.fromisoformat(request.date)
            target_date_str = request.date
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        async def event_generator():
            yield ":" + " " * 4096 + "\n\n"
            
            debug("SSE stream: Kickoff")
            yield f"data: {json.dumps({'status': 'processing', 'message': '生成の準備ができました'})}\n\n"
            
            try:
                pw = ProgressWrapper()
                
                async def run_work():
                    try:
                        await process_daily_diary(target_date_str, pw.callback)
                    finally:
                        await pw.callback("__DONE__")

                work_task = asyncio.create_task(run_work())
                
                while True:
                    try:
                        msg = await asyncio.wait_for(pw.queue.get(), timeout=15.0)
                        if msg == "__DONE__":
                            debug("SSE stream: Done signal received")
                            break
                        debug(f"SSE stream: Yielding message: {msg}")
                        yield f"data: {json.dumps({'status': 'processing', 'message': msg})}\n\n"
                    except asyncio.TimeoutError:
                        debug("SSE stream: Yielding ping")
                        yield f": ping\n\n"
                
                await work_task
                yield f"data: {json.dumps({'status': 'completed', 'message': '完了しました'})}\n\n"
            except Exception as e:
                error(f"Streaming generation failed: {e}", exc_info=True)
                yield f"data: {json.dumps({'status': 'failed', 'message': str(e)})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Transfer-Encoding": "chunked",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error starting manual diary generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/diary/list")
async def list_diaries(limit: int = 30, offset: int = 0):
    if get_all_diaries is None:
        raise HTTPException(status_code=503, detail="Diary service not available")
    
    try:
        diaries = get_all_diaries(limit=limit, offset=offset)
        for diary in diaries:
            if diary.get("plant_image_url") and diary["plant_image_url"].startswith("gs://"):
                diary["plant_image_url"] = f"/api/diary/image/{diary['date']}"
        return {"diaries": diaries}
    except Exception as e:
        error(f"Error listing diaries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/diary/{date}")
async def get_diary(date: str):
    if get_diary_by_date is None:
        raise HTTPException(status_code=503, detail="Diary service not available")
    
    try:
        diary = get_diary_by_date(date)
        
        if diary is None:
            raise HTTPException(status_code=404, detail="Diary not found")
        
        if diary.get("plant_image_url") and diary["plant_image_url"].startswith("gs://"):
            diary["plant_image_url"] = f"/api/diary/image/{diary['date']}"
            
        return diary
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error fetching diary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/diary/image/{date}")
async def get_diary_image(date: str):
    """
    Serve diary image from GCS via proxy.
    """
    if get_diary_by_date is None:
        raise HTTPException(status_code=503, detail="Diary service not available")
    
    try:
        diary = get_diary_by_date(date)
        if not diary or not diary.get("plant_image_url") or not diary["plant_image_url"].startswith("gs://"):
            raise HTTPException(status_code=404, detail="Image not found or not in GCS format")
        
        gcs_uri = diary["plant_image_url"]
        path_without_scheme = gcs_uri[5:]
        parts = path_without_scheme.split("/", 1)
        if len(parts) < 2:
            raise HTTPException(status_code=400, detail="Invalid GCS URI")
        
        bucket_name = parts[0]
        blob_name = parts[1]
        
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        if not blob.exists():
            raise HTTPException(status_code=404, detail="Image blob not found in GCS")
            
        img_bytes = blob.download_as_bytes()
        from fastapi import Response
        return Response(content=img_bytes, media_type="image/png")
        
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error serving diary image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/seed-guide/image/{job_id}/{step_index}")
async def get_seed_guide_image(job_id: str, step_index: int):
    """
    Serve seed guide step image from GCS via proxy.
    """
    try:
        bucket_name = "ai-agentic-hackathon-4-bk"
        # Search for blob starting with "seed-guides/output/{job_id}_" and ending with "_{step_index}.jpg"
        prefix = f"seed-guides/output/{job_id}_"
        
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        # Use prefix for efficient listing
        blobs = bucket.list_blobs(prefix=prefix)
        
        target_suffix = f"_{step_index}.jpg"
        target_blob = None
        for blob in blobs:
            if blob.name.endswith(target_suffix):
                target_blob = blob
                break
        
        if not target_blob:
             raise HTTPException(status_code=404, detail=f"Image for step {step_index} not found")
             
        img_bytes = await asyncio.to_thread(target_blob.download_as_bytes)
        from fastapi import Response
        return Response(content=img_bytes, media_type="image/jpeg")
        
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error serving seed guide image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/diary/generate-daily")
async def generate_daily_diary_endpoint(background_tasks: BackgroundTasks):
    """
    Trigger daily diary generation.
    """
    if process_daily_diary is None:
        raise HTTPException(status_code=503, detail="Diary service not available")
    
    try:
        from datetime import datetime, timedelta
        target_date = (datetime.now() - timedelta(hours=1)).date()
        background_tasks.add_task(process_daily_diary, target_date.isoformat())
        return {
            "status": "accepted",
            "date": target_date.isoformat(),
            "message": "Diary generation started"
        }
    except Exception as e:
        error(f"Error starting diary generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/character")
async def get_character_metadata():
    """
    Get the current character metadata.
    Proxies the GCS image URL to a local API URL.
    """
    try:
        doc_ref = db.collection("growing_diaries").document("Character")
        doc = await doc_ref.get()
        
        if not doc.exists:
            # Return empty if not found, or 404
            return {}
            
        data = doc.to_dict()
        
        # Transform image_uri to proxy URL
        if data.get("image_uri") and data["image_uri"].startswith("https://storage.googleapis.com/"):
            gcs_uri = data["image_uri"]
            bucket_name = "ai-agentic-hackathon-4-bk"
            prefix = f"https://storage.googleapis.com/{bucket_name}/"
            
            if gcs_uri.startswith(prefix):
                blob_path = gcs_uri[len(prefix):]
                import urllib.parse
                encoded_path = urllib.parse.quote(blob_path)
                data["image_uri"] = f"/api/character/image?path={encoded_path}"
                
        return data
    except Exception as e:
        error(f"Error fetching character: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/character/image")
async def get_character_image_endpoint(path: str):
    """
    Serve character image from GCS via proxy.
    path: Relative path in GCS bucket (e.g. characters/xyz.png)
    """
    try:
        bucket_name = "ai-agentic-hackathon-4-bk"
        
        # Security check: prevent path traversal or accessing other buckets? 
        # GCS paths don't use .. usually, but good to be safe. 
        # We assume path is just the object name.
        
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(path)
        
        if not blob.exists():
            raise HTTPException(status_code=404, detail="Image not found")
            
        img_bytes = blob.download_as_bytes()
        from fastapi import Response
        return Response(content=img_bytes, media_type="image/png")
        
    except HTTPException:
        raise
    except Exception as e:
        error(f"Error serving character image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Unified Seed Feature Endpoints ---

@app.post("/api/unified/start")
async def start_unified_job(background_tasks: BackgroundTasks, file: UploadFile = File(...), research_mode: str = "agent", image_model: str = "pro", guide_image_mode: str = "single"):
    """
    Unified endpoint to start Research, Guide, and Character generation from a single image.
    """
    try:
        # 1. Read and Upload Image to GCS (Standardize on one upload)
        content = await file.read()
        job_id = str(uuid.uuid4())
        timestamp = int(time.time())
        safe_filename = file.filename.replace(" ", "_").replace("/", "_")
        bucket_name = "ai-agentic-hackathon-4-bk"
        blob_name = f"unified/input/{timestamp}_{job_id}_{safe_filename}"
        
        info(f"[Unified] start job={job_id} file={file.filename}")
        info(f"[Unified] upload_input job={job_id} blob={blob_name}")
        
        image_url = await asyncio.to_thread(
            _upload_to_gcs_sync,
            bucket_name,
            blob_name,
            content,
            file.content_type
        )
        
        # 2. Initialize Sub-Jobs
        
        # A. Research (Vegetable Status)
        # We need to do a quick analysis first to get the name, OR just use "Unknown" and let the background task refine it.
        # process_research expects doc_id, vegetable_name, analysis_data.
        # Let's do a quick analysis here synchronously? Or is it too slow?
        # analyze_seed_packet is relatively fast (Gemini Flash). 
        # But for "Unified" experience, maybe we return immediately.
        # However, init_vegetable_status needs a name.
        # Let's use "Pending Analysis" as name and let the background task update it?
        # Actually checking process_research: it takes vegetable_name arg but also analysis_data.
        # Let's run the analysis in background too? 
        # existing /api/register-seed runs analyze_seed_packet synchronously... 
        # For better UX (speed), let's push it to background. But we need a doc ID.
        
        # Let's create the documents first.
        
        # Research Doc
        research_doc_id = init_vegetable_status("Analyzing...")
        
        # Guide Job Doc
        guide_job_id = f"guide-{job_id}"
        guide_doc_ref = db.collection("seed_guide_jobs").document(guide_job_id)
        await guide_doc_ref.set({
            "job_id": guide_job_id,
            "title": "Unified Seed Guide",
            "status": "PENDING",
            "message": "Waiting for unified worker...",
            "input_image_url": image_url,
            "result": None,
            "steps": [],
            "created_at": firestore.SERVER_TIMESTAMP
        })
        
        # Character Job Doc
        char_job_id = f"char-{job_id}"
        char_doc_ref = db.collection("character_jobs").document(char_job_id)
        await char_doc_ref.set({
            "job_id": char_job_id,
            "status": "PENDING",
            "message": "Waiting for unified worker...",
            "result": None,
            "created_at": firestore.SERVER_TIMESTAMP,
            "type": "character"
        })
        
        # 3. Create Unified Job Tracker
        unified_doc_ref = db.collection("unified_jobs").document(job_id)
        await unified_doc_ref.set({
            "job_id": job_id,
            "created_at": firestore.SERVER_TIMESTAMP,
            "research_doc_id": research_doc_id,
            "guide_job_id": guide_job_id,
            "char_job_id": char_job_id,
            "image_url": image_url,
            "status": "PROCESSING"
        })
        
        info(
            f"[Unified] created docs job={job_id} research={research_doc_id} "
            f"guide={guide_job_id} char={char_job_id}"
        )

        # 4. Queue Background Tasks (Parallel Execution)
        
        async def unified_runner():
            # Phase 1: Character Generation + Basic Seed Analysis (Parallel)
            info(f"[Unified] phase1 start job={job_id} (character + basic_analysis)")
            
            # We need to run analyze_seed_packet and store the result for Phase 2
            # We'll use a local helper for the research part to extract data first
            
            async def phase1_basic_analysis():
                set_session_id(f"uni-res-{job_id[:8]}")
                try:
                    info(f"[Unified][LLM] analyze_seed_packet start job={job_id} research={research_doc_id}")
                    start_ts = time.time()
                    packet_analysis_json = await asyncio.to_thread(analyze_seed_packet, content) # content is image bytes
                    elapsed_ms = (time.time() - start_ts) * 1000
                    info(
                        f"[Unified][LLM] analyze_seed_packet done job={job_id} "
                        f"research={research_doc_id} ms={elapsed_ms:.0f}"
                    )
                    
                    try:
                        clean_text = packet_analysis_json.replace("```json", "").replace("```", "")
                        analysis_data = json.loads(clean_text)
                        vegetable_name = analysis_data.get("name", "Unknown Vegetable")
                        # Check if "unknown"
                        if vegetable_name.lower() == "unknown":
                            error_msg = analysis_data.get("visible_instructions", "野菜の種類を特定できませんでした。")
                            warning(
                                f"[Unified] unknown_vegetable job={job_id} "
                                f"research={research_doc_id} msg={error_msg}"
                            )
                            await db.collection("vegetables").document(research_doc_id).set({
                                "status": "failed",
                                "error": error_msg,
                                "updated_at": firestore.SERVER_TIMESTAMP
                            }, merge=True)
                            return None, None

                        # SAVE IMMEDIATELY to Firestore so frontend sees it
                        # We use the research_doc_id in "vegetables" collection
                        # Structure it inside 'result' so frontend checks pass
                        await db.collection("vegetables").document(research_doc_id).set({
                            "name": vegetable_name,
                            "result": {
                                "name": vegetable_name,
                                "difficulty_level": analysis_data.get("difficulty_level"),
                                "optimal_temp_range": analysis_data.get("optimal_temp_range"),
                                "basic_analysis": analysis_data # Keep raw data here too
                            },
                            "status": "researching", 
                            "updated_at": firestore.SERVER_TIMESTAMP
                        }, merge=True)
                        info(
                            f"[Unified] basic_analysis_saved job={job_id} "
                            f"research={research_doc_id} veg={vegetable_name}"
                        )
                        
                    except:
                        vegetable_name = "Unknown Vegetable"
                        analysis_data = {"raw": packet_analysis_json}
                        
                    return vegetable_name, analysis_data
                except Exception as e:
                    error(f"[Unified] basic_analysis_failed job={job_id} error={e}")
                    update_vegetable_status(research_doc_id, "failed", {"error": str(e)})
                    return None, None

            # Run Phase 1
            # Character runs in background (fire and forget? No, we await it if we want to ensure it completes, 
            # but user said order is Char -> Research -> Guide, so maybe Char should finish before Research?
            # User said: "Character Creation & Overview -> Detailed Research -> Guide"
            # So Char and Overview (Basic Analysis) are first.
            
            char_task = process_character_generation(char_job_id, content)
            basic_analysis_task = phase1_basic_analysis()
            
            # Wait for both? Or just wait for Basic Analysis to start Research?
            # If we wait for both, Character timing affects Research start.
            # "Character Creation... -> Detailed Research" implies sequence or at least grouping.
            # Let's await both to be safe and clean.
            
            results = await asyncio.gather(char_task, basic_analysis_task)
            veg_name, analysis_data = results[1]
            
            if not veg_name:
                warning(
                    f"[Unified] abort job={job_id} reason=basic_analysis_failed_or_unknown"
                )
                # Ensure research job is marked as failed if not already (handled in phase1_basic_analysis but good to be safe)
                # Also, we should probably mark unified job as failed?
                # But individual status is what frontend checks.
                return

            # Phase 2 & 3: Deep Research + Cultivation Guide (Parallel)
            info(
                f"[Unified] phase2_3 start job={job_id} veg={veg_name}"
            )

            info(f"[Unified][LLM] deep_research start job={job_id} research={research_doc_id} mode={research_mode}")
            research_start_ts = time.time()
            research_task = asyncio.to_thread(process_research, research_doc_id, veg_name, analysis_data, mode=research_mode)
            guide_task = process_seed_guide(guide_job_id, blob_name, image_model=image_model, guide_image_mode=guide_image_mode)
            research_result, guide_result = await asyncio.gather(
                research_task,
                guide_task,
                return_exceptions=True
            )

            research_elapsed_ms = (time.time() - research_start_ts) * 1000
            info(
                f"[Unified][LLM] deep_research done job={job_id} "
                f"research={research_doc_id} ms={research_elapsed_ms:.0f}"
            )

            if isinstance(research_result, Exception):
                error(f"[Unified] phase2_failed job={job_id} error={research_result}")
            if isinstance(guide_result, Exception):
                error(f"[Unified] phase3_failed job={job_id} error={guide_result}")

            info(f"[Unified] done job={job_id}")

        # Add single orchestrator task
        background_tasks.add_task(unified_runner)
        
        return {
            "status": "accepted", 
            "job_id": job_id,
            "research_id": research_doc_id,
            "guide_id": guide_job_id,
            "character_id": char_job_id
        }

    except Exception as e:
        error(f"Unified start failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/unified/jobs/{job_id}")
async def get_unified_job_status(job_id: str):
    """
    Returns the consolidated status of a unified job.
    """
    try:
        # 1. Get Unified Doc
        doc_ref = db.collection("unified_jobs").document(job_id)
        doc = await doc_ref.get()
        if not doc.exists:
             raise HTTPException(status_code=404, detail="Unified Job not found")
        
        data = doc.to_dict()
        
        # 2. Fetch Sub-Job Statuses in Parallel
        research_id = data.get("research_doc_id")
        guide_id = data.get("guide_job_id")
        char_id = data.get("char_job_id")
        
        results = {
            "job_id": job_id,
            "created_at": data.get("created_at"),
            "image_url": data.get("image_url"),
            "research": {"status": "PENDING"},
            "guide": {"status": "PENDING"},
            "character": {"status": "PENDING"}
        }
        
        async def fetch_research():
            if not research_id: return None
            # Research docs are in "vegetables" collection
            d = await db.collection("vegetables").document(research_id).get()
            return d.to_dict() if d.exists else None

        async def fetch_guide():
            if not guide_id: return None
            # Guide jobs in "seed_guide_jobs"
            d = await db.collection("seed_guide_jobs").document(guide_id).get()
            return d.to_dict() if d.exists else None
            
        async def fetch_char():
            if not char_id: return None
             # Char jobs in "character_jobs"
            d = await db.collection("character_jobs").document(char_id).get()
            return d.to_dict() if d.exists else None
        
        r_data, g_data, c_data = await asyncio.gather(fetch_research(), fetch_guide(), fetch_char())
        
        if r_data:
            # Normalize status to uppercase for frontend
            if "status" in r_data:
                r_data["status"] = r_data["status"].upper()
            # Include the research doc ID so frontend can apply it to edge agent
            r_data["id"] = research_id
            results["research"] = make_serializable(r_data)
        if g_data:
            # Handle guide image proxying like in other endpoints if needed, but for now just raw
            # Guide endpoint logic:
            results["guide"] = make_serializable(g_data)
            
            # Transform Step Image URLs to Proxy URLs
            if results["guide"].get("result") and isinstance(results["guide"]["result"], list):
                bucket_name = "ai-agentic-hackathon-4-bk"
                prefix = f"https://storage.googleapis.com/{bucket_name}/"
                
                for step in results["guide"]["result"]:
                    if isinstance(step, dict) and step.get("image_url"):
                        gcs_uri = step["image_url"]
                        if gcs_uri.startswith(prefix):
                            blob_path = gcs_uri[len(prefix):]
                            import urllib.parse
                            encoded_path = urllib.parse.quote(blob_path)
                            step["image_url"] = f"/api/character/image?path={encoded_path}"
        if c_data:
            # Transform image_uri to proxy URL if it's a GCS URL
            # The character document saves 'image_uri' but the result might have 'image_url' or 'image_uri'
            # Let's check 'image_url' in result or 'image_uri' in top level
            
            # The structure in process_character_generation saves:
            # result = { ... "image_url": "https://..." }
            # So c_data["result"]["image_url"] should be the target if it exists
            
            if c_data.get("result") and isinstance(c_data["result"], dict):
                char_result = c_data["result"]
                gcs_uri = char_result.get("image_url")
                
                if gcs_uri and gcs_uri.startswith("https://storage.googleapis.com/"):
                    bucket_name = "ai-agentic-hackathon-4-bk"
                    prefix = f"https://storage.googleapis.com/{bucket_name}/"
                    
                    if gcs_uri.startswith(prefix):
                        blob_path = gcs_uri[len(prefix):]
                        import urllib.parse
                        encoded_path = urllib.parse.quote(blob_path)
                        char_result["image_url"] = f"/api/character/image?path={encoded_path}"
                        
            results["character"] = make_serializable(c_data)
            # Include the character job ID so frontend can select it for diary
            results["character"]["id"] = char_id
            
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        error(f"Unified status fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def make_serializable(obj):
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(v) for v in obj]
    elif hasattr(obj, 'isoformat'):
        return obj.isoformat()
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        return str(obj)

@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    startup_session = generate_session_id()
    set_session_id(startup_session)
    set_request_id("startup")
    info("AI Batake Backend started successfully")
    info(f"Project ID: {project_id}")
    info(f"Firestore collection: {COLLECTION_NAME}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)

