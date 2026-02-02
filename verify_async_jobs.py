import requests
import time
import sys
import os

BASE_URL = "http://localhost:8082"

def get_test_image():
    from PIL import Image
    import io
    # Create a small blank image
    img = Image.new('RGB', (100, 100), color = 'green')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr

def verify_async_flow():
    print(f"Testing Async API at {BASE_URL}...")
    
    # 1. Start Job
    print("1. Starting Job (POST /api/seed-guide/jobs)...")
    files = {'file': ('test.jpg', get_test_image(), 'image/jpeg')}
    try:
        response = requests.post(f"{BASE_URL}/api/seed-guide/jobs", files=files)
        if response.status_code != 200:
            print(f"FAILED to start job: {response.status_code} {response.text}")
            sys.exit(1)
        
        data = response.json()
        job_id = data.get("job_id")
        print(f"Job Initialized! ID: {job_id}")
    except requests.exceptions.ConnectionError:
        print("FAILED: Connection refused. Is the server running?")
        sys.exit(1)

    # 2. Poll Status
    print("2. Polling Status (GET /api/seed-guide/jobs/{job_id})...")
    status = "PENDING"
    last_message = ""
    start_time = time.time()
    
    while status in ["PENDING", "PROCESSING"]:
        # Timeout safety (e.g. 5 minutes)
        if time.time() - start_time > 300:
            print("TIMEOUT: Job took too long.")
            sys.exit(1)
            
        time.sleep(2)
        resp = requests.get(f"{BASE_URL}/api/seed-guide/jobs/{job_id}")
        if resp.status_code != 200:
            print(f"Polling Error: {resp.status_code}")
            continue
            
        job_data = resp.json()
        status = job_data.get("status")
        message = job_data.get("message")
        
        if message != last_message:
            print(f"Status: {status} | Message: {message}")
            last_message = message
    
    # 3. Verify Result
    if status == "COMPLETED":
        result = job_data.get("result")
        print(f"\nSUCCESS! Job Completed.")
        print(f"Result contains {len(result)} steps.")
        print("Steps:")
        for step in result:
             print(f"- {step.get('step_title')}")
    else:
        print(f"\nFAILED! Job ended with status: {status}")
        print(f"Message: {job_data.get('message')}")
        sys.exit(1)

if __name__ == "__main__":
    verify_async_flow()
