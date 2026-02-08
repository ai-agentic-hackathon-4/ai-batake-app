
import asyncio
import os
import sys

# Add parent dir to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import db, _upload_to_gcs_sync
from google.cloud import firestore

async def verify_character_save():
    print("Verifying Character Save Logic...")
    
    # Mock data
    mock_result = {
        "character_name": "Test Character",
        "personality": "Cheerful and sunny",
        "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==" # 1x1 red pixel
    }
    job_id = "test-job-id"
    
    try:
        if not db:
            print("Firestore not initialized.")
            return

        print("1. Mocking GCS Upload...")
        # We can't easily mock the internal logic of process_character_generation without running the whole app or extensive mocking.
        # Instead, let's verify the snippet logic directly.
        
        import base64
        import time
        
        b64_data = mock_result["image_base64"]
        img_data = base64.b64decode(b64_data)
        timestamp = int(time.time())
        blob_name = f"characters/TEST_{job_id}_{timestamp}.png"
        
        print(f"   Uploading to {blob_name}...")
        image_url = await asyncio.to_thread(
            _upload_to_gcs_sync, 
            "ai-agentic-hackathon-4-bk", 
            blob_name, 
            img_data, 
            "image/png"
        )
        print(f"   Upload successful: {image_url}")
        
        print("2. Mocking Firestore Update...")
        char_doc_ref = db.collection("growing_diaries").document("Character")
        await char_doc_ref.set({
            "name": mock_result.get("character_name"),
            "image_uri": image_url,
            "personality": mock_result.get("personality"),
            "updated_at": firestore.SERVER_TIMESTAMP
        }, merge=True)
        print("   Firestore update successful.")
        
        # Verify read
        doc = await char_doc_ref.get()
        data = doc.to_dict()
        print(f"   Read back data: {data}")
        
        assert data["name"] == "Test Character"
        assert data["image_uri"] == image_url
        
        print("\nSUCCESS: Logic verified.")
        
    except Exception as e:
        print(f"\nFAILED: {e}")

if __name__ == "__main__":
    asyncio.run(verify_character_save())
