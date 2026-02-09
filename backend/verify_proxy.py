
import asyncio
import os
import sys
import urllib.parse
from google.cloud import storage

# Add parent dir to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import db

async def verify_proxy_logic():
    print("Verifying Proxy Logic...")
    
    if not db:
        print("Firestore not initialized.")
        return

    # 1. Simulate GET /api/character
    print("\n1. Testing GET /api/character logic...")
    doc_ref = db.collection("growing_diaries").document("Character")
    doc = await doc_ref.get()
    
    if not doc.exists:
        print("Character document not found!")
        return
        
    data = doc.to_dict()
    print(f"   Original Data: {data}")
    
    image_uri = data.get("image_uri")
    proxy_url = None
    blob_path = None
    
    if image_uri and image_uri.startswith("https://storage.googleapis.com/"):
        bucket_name = "ai-agentic-hackathon-4-bk"
        prefix = f"https://storage.googleapis.com/{bucket_name}/"
        
        if image_uri.startswith(prefix):
            blob_path = image_uri[len(prefix):]
            encoded_path = urllib.parse.quote(blob_path)
            proxy_url = f"/api/character/image?path={encoded_path}"
            print(f"   Transformed URL: {proxy_url}")
            print(f"   Extracted Path: {blob_path}")
        else:
            print("   URI format doesn't match expected bucket prefix.")
    else:
        print("   No image_uri or invalid format.")
        
    # 2. Simulate GET /api/character/image
    print("\n2. Testing GET /api/character/image logic...")
    if blob_path:
        print(f"   Attempting to download from GCS path: {blob_path}")
        try:
            client = storage.Client()
            bucket = client.bucket("ai-agentic-hackathon-4-bk")
            blob = bucket.blob(blob_path)
            
            if blob.exists():
                print("   Blob exists!")
                content = blob.download_as_bytes()
                print(f"   Downloaded {len(content)} bytes.")
                print("SUCCESS: Proxy logic verified.")
            else:
                print("FAILED: Blob does not exist.")
        except Exception as e:
            print(f"FAILED: GCS Error: {e}")
    else:
        print("Skipping download test due to extraction failure.")

    # 3. Simulate Job Result Transformation Logic
    print("\n3. Testing Job Result Transformation Logic...")
    mock_job_result = {
        "status": "COMPLETED",
        "result": {
            "image_url": "https://storage.googleapis.com/ai-agentic-hackathon-4-bk/characters/TEST_JOB_IMG.png",
            "image_base64": "remove_me"
        }
    }
    
    res = mock_job_result["result"]
    if res.get("image_url") and res["image_url"].startswith("https://storage.googleapis.com/"):
        gcs_uri = res["image_url"]
        bucket_name = "ai-agentic-hackathon-4-bk"
        prefix = f"https://storage.googleapis.com/{bucket_name}/"
        
        if gcs_uri.startswith(prefix):
            blob_path = gcs_uri[len(prefix):]
            encoded_path = urllib.parse.quote(blob_path)
            res["image_url"] = f"/api/character/image?path={encoded_path}"
            if "image_base64" in res:
                del res["image_base64"]
                
    print(f"   Transformed Result: {res}")
    
    expected_url = f"/api/character/image?path={urllib.parse.quote('characters/TEST_JOB_IMG.png')}"
    if res["image_url"] == expected_url and "image_base64" not in res:
        print("SUCCESS: Job transformation logic verified.")
    else:
        print(f"FAILED: Transformation mismatch. Expected {expected_url}, got {res['image_url']}")

if __name__ == "__main__":
    asyncio.run(verify_proxy_logic())
