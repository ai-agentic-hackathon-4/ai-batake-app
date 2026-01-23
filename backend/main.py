from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
try:
    from .db import save_growing_instructions
    from .research_agent import analyze_seed_packet, perform_deep_research
    # from .agent import get_weather_from_agent
except ImportError:
    # When running directly as a script
    from db import save_growing_instructions
    from research_agent import analyze_seed_packet, perform_deep_research
    # from agent import get_weather_from_agent
import logging
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

class WeatherRequest(BaseModel):
    region: str

# @app.post("/api/weather")
# async def get_weather(request: WeatherRequest):
#     try:
#         weather_info = get_weather_from_agent(request.region)
#         return {"message": weather_info}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

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
        
        # Parse analysis result (assuming it returns JSON string or dictionary)
        # The agent returns a string, we might need to be careful or parse it.
        # Ideally analyze_seed_packet should return a dict or we parse it here.
        # For simplicity, let's treat the text specifically or expect JSON in text.
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
