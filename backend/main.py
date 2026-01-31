from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
import os
from google.cloud import firestore
from .agent import get_weather_from_agent
from .seed_service import analyze_seed_and_generate_guide

app = FastAPI()

# Firestore Client (Async)
# Ensure GOOGLE_CLOUD_PROJECT is set, or it will try to resolve from env/metadata
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
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

async def process_seed_guide(job_id: str, image_bytes: bytes):
    """Background task to process seed guide generation."""
    doc_ref = db.collection(COLLECTION_NAME).document(job_id)
    
    # Update status to PROCESSING
    await doc_ref.update({
        "status": "PROCESSING",
        "message": "Starting analysis..."
    })
    
    async def progress_callback(msg: str):
        print(f"[Job {job_id}] {msg}")
        # Update progress in Firestore
        await doc_ref.update({"message": msg})

    try:
        steps = await analyze_seed_and_generate_guide(image_bytes, progress_callback)
        # Verify JSON serializability?
        # steps is a list of dicts, should be fine for Firestore.
        await doc_ref.update({
            "status": "COMPLETED",
            "result": steps,
            "message": "Complete!"
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
    """Starts an async job to generate the seed guide."""
    try:
        content = await file.read()
        job_id = str(uuid.uuid4())
        
        # Initialize Job in Firestore
        doc_ref = db.collection(COLLECTION_NAME).document(job_id)
        await doc_ref.set({
            "job_id": job_id,
            "status": "PENDING",
            "message": "Job created, waiting for worker...",
            "result": None,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        
        # Start Background Task
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
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
