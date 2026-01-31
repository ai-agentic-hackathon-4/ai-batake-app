from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from .agent import get_weather_from_agent
from .seed_service import analyze_seed_and_generate_guide

app = FastAPI()

class WeatherRequest(BaseModel):
    region: str

@app.post("/api/weather")
async def get_weather(request: WeatherRequest):
    try:
        weather_info = get_weather_from_agent(request.region)
        return {"message": weather_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/seed-guide")
async def generate_seed_guide(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        # Analyze and Generate
        steps = await analyze_seed_and_generate_guide(contents)
        return {"steps": steps}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate guide: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
