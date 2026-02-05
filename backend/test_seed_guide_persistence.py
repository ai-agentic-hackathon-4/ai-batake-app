from fastapi.testclient import TestClient
from main import app
import os
import sys
import json
import base64

# Add backend to path if running from backend dir or parent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

client = TestClient(app)

def test_persistence_flow():
    print("--- Testing Seed Guide Persistence ---")
    
    # 1. Mock Data
    mock_steps = [
        {
            "title": "Test Step 1",
            "description": "Plant the seed deep.",
            "image_base64": "mock_base64_string",
            "image_prompt": "A seed in dirt"
        },
        {
            "title": "Test Step 2",
            "description": "Water it well.",
            "image_base64": "mock_base64_string_2",
            "image_prompt": "Watering can"
        }
    ]
    
    payload = {
        "title": "Test Guide",
        "description": "A test guide for verification.",
        "steps": mock_steps,
        "original_image": "mock_original_image_b64"
    }
    
    # 2. Test Save
    print("\n[1] Testing Save Endpoint...")
    response = client.post("/api/seed-guide/save", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
        
    data = response.json()
    doc_id = data.get("id")
    print(f"Saved Guide ID: {doc_id}")
    assert doc_id is not None
    
    # 3. Test List
    print("\n[2] Testing List Endpoint...")
    response = client.get("/api/seed-guide/saved")
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
        
    guides = response.json()
    print(f"Found {len(guides)} guides.")
    
    found = False
    for g in guides:
        if g['id'] == doc_id:
            found = True
            print(f"Found our saved guide in list: {g['title']}")
            break
    
    if not found:
        print("ERROR: Saved guide not found in list.")
        
    # 4. Test Get Detail
    print("\n[3] Testing Get Detail Endpoint...")
    response = client.get(f"/api/seed-guide/saved/{doc_id}")
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
        
    detail = response.json()
    print(f"Retrieved Title: {detail.get('title')}")
    print(f"Retrieved Steps: {len(detail.get('steps', []))}")
    
    assert detail.get('title') == "Test Guide"
    assert len(detail.get('steps')) == 2
    
    print("\n--- Verification Complete: SUCCESS ---")

if __name__ == "__main__":
    test_persistence_flow()
