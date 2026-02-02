import requests
from PIL import Image
import io
import time
import sys

URL = "http://localhost:8082/api/register-seed"

def create_dummy_image():
    # Create a small blank image
    img = Image.new('RGB', (100, 100), color = 'brown')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr

def test_api():
    print(f"Testing API at {URL}...")
    try:
        img_data = create_dummy_image()
        files = {'file': ('seed.jpg', img_data, 'image/jpeg')}
        
        # We expect this to call Vertex AI. 
        # If credentials are not set in the container, it will fail with 500.
        # But we want to verify the Endpoint logic itself.
        
        # Note: In this environment, we might verify connection and handling.
        start = time.time()
        response = requests.post(URL, files=files, timeout=300)
        end = time.time()
        
        print(f"Status Code: {response.status_code}")
        print(f"Time Taken: {end - start:.2f}s")
        print(f"Response: {response.text[:500]}...") # Print first 500 chars
        
        if response.status_code == 200:
            print("SUCCESS: API returned 200")
            json_resp = response.json()
            if "document_id" in json_resp:
                print(f"Document ID: {json_resp['document_id']}")
                print(f"Vegetable: {json_resp.get('vegetable')}")
            else:
                print("WARNING: 'document_id' key missing.")
        else:
            print("FAILURE: API did not return 200")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_api()
