from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
try:
    from .db import save_growing_instructions, get_latest_vegetable, get_sensor_history, get_recent_sensor_logs
    from .db import save_growing_instructions, get_latest_vegetable, get_sensor_history, get_recent_sensor_logs
    from .research_agent import analyze_seed_packet, perform_deep_research
    from .agent import get_weather_from_agent
except ImportError:
    # When running directly as a script
    from db import save_growing_instructions, get_latest_vegetable, get_sensor_history, get_recent_sensor_logs
    from research_agent import analyze_seed_packet, perform_deep_research
    from research_agent import analyze_seed_packet, perform_deep_research
    from agent import get_weather_from_agent
import logging
import base64
from google.cloud import storage
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin (e.g. localhost:3000)
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

@app.get("/api/vegetables/latest")
async def get_latest_vegetable_endpoint():
    try:
        data = get_latest_vegetable()
        if data:
            return data
        else:
            # Return empty object or specific message if no data, or 404
            # user just wants to "display 1 item", so 404 is appropriate if truly empty
            return {} 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/register-seed")
async def register_seed(file: UploadFile = File(...)):
    """
    Receives a seed packet image, analyzes it, researches growing methods,
    and saves the instructions to Firestore.
    """
    try:
        # Read image
        content = await file.read()
        
        # 1. Analyze Seed Packet (Gemini Vision)
        logging.info("Analyzing seed packet image...")
        packet_analysis_json = analyze_seed_packet(content)
        
        # Parse analysis result
        import json
        try:
            # Simple soft parsing if the model returns markdown code block 
            clean_text = packet_analysis_json.replace("```json", "").replace("```", "")
            analysis_data = json.loads(clean_text)
            vegetable_name = analysis_data.get("name", "Unknown Vegetable")
        except:
            vegetable_name = "Unknown Vegetable"
            analysis_data = {"raw": packet_analysis_json}
            
        logging.info(f"Identified vegetable: {vegetable_name}")
        
        # 2. Deep Research
        logging.info(f"Performing deep research for: {vegetable_name}")
        research_result = perform_deep_research(vegetable_name, str(analysis_data))
        
        # 3. Save to Firestore
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
