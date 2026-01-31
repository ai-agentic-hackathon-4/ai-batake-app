from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import os
import json
import base64
from dotenv import load_dotenv
from google.cloud import storage

try:
    from .db import init_vegetable_status, update_vegetable_status, get_all_vegetables, update_edge_agent_config, get_latest_vegetable, get_sensor_history, get_recent_sensor_logs
    from .research_agent import analyze_seed_packet, perform_deep_research
    from .agent import get_weather_from_agent
except ImportError:
    # When running directly as a script
    from db import init_vegetable_status, update_vegetable_status, get_all_vegetables, update_edge_agent_config, get_latest_vegetable, get_sensor_history, get_recent_sensor_logs
    from research_agent import analyze_seed_packet, perform_deep_research
    from agent import get_weather_from_agent

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        # Get most recent 1 log
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

@app.get("/api/plant-camera/latest")
async def get_latest_plant_image():
    try:
        # Initialize client
        storage_client = storage.Client()
        bucket_name = "ai-agentic-hackathon-4-bk"
        bucket = storage_client.bucket(bucket_name)

        # List blobs in the directory
        prefix = "logger-captures/"
        blobs = list(bucket.list_blobs(prefix=prefix))

        if not blobs:
            return {"error": "No images found"}
        
        # Sort by created time
        # Filter out directories
        image_blobs = [b for b in blobs if not b.name.endswith('/')]
        
        if not image_blobs:
            return {"error": "No image files found"}

        # Get latest
        latest_blob = max(image_blobs, key=lambda b: b.time_created)
        
        # Download as bytes
        image_data = latest_blob.download_as_bytes()
        
        # Encode to base64
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
        
        # Update Edge Agent Configuration
        update_edge_agent_config(research_result)
        
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

@app.get("/api/vegetables")
async def list_vegetables():
    """Returns list of all vegetables with current status."""
    return get_all_vegetables()

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
