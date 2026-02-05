from fastapi.testclient import TestClient
from main import app
import os
import sys
import time

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

client = TestClient(app)

def test_async_generation_flow():
    print("--- Testing Async Persistence Flow ---")
    
    # 1. Start Generation (Mocking file upload)
    print("\n[1] Starting Generation...")
    # Create a dummy image file
    files = {'file': ('test_seed.jpg', b'fake_image_content', 'image/jpeg')}
    
    response = client.post("/api/seed-guide/generate", files=files)
    print(f"Start Response Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
        
    data = response.json()
    job_id = data.get("job_id")
    print(f"Job/Guide ID: {job_id}")
    print(f"Initial Status: {data.get('status')}")
    
    if not job_id:
        print("Failed to get job_id")
        return

    # 2. Verify it exists in "Saved Guides" immediately
    print("\n[2] Checking Saved Guides List...")
    response = client.get(f"/api/seed-guide/saved/{job_id}")
    print(f"Get Response Status: {response.status_code}")
    
    if response.status_code == 200:
        guide = response.json()
        print(f"Found Guide in DB!")
        print(f"ID: {guide.get('id')}")
        print(f"Status: {guide.get('status')}")
        print(f"Message: {guide.get('message')}")
        
        # Expect PENDING or PROCESSING (background task might have started)
        expected_statuses = ["PENDING", "PROCESSING", "COMPLETED", "FAILED"]
        if guide.get("status") in expected_statuses:
             print("SUCCESS: Guide persisted immediately with valid status.")
        else:
             print(f"FAILURE: Unexpected status structure: {guide}")
    else:
        print("FAILURE: Guide not found in persisted storage.")

    print("\n--- Testing Complete ---")

if __name__ == "__main__":
    test_async_generation_flow()
