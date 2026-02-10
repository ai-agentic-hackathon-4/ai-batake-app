
import requests
import sys
import time
import json
import os

BASE_URL = "http://localhost:8081"

def test_unified_flow(image_path):
    print(f"Testing Unified Flow with image: {image_path}")
    
    # 1. Start Job
    url = f"{BASE_URL}/api/unified/start"
    files = {'file': open(image_path, 'rb')}
    
    try:
        print(f"POST {url}...")
        response = requests.post(url, files=files)
        response.raise_for_status()
        data = response.json()
        print(f"Start Response: {json.dumps(data, indent=2)}")
        
        job_id = data.get("job_id")
        if not job_id:
            print("ERROR: No job_id returned")
            return
            
        print(f"Job ID: {job_id}")
        
    except Exception as e:
        print(f"Failed to start job: {e}")
        try:
            print(f"Response text: {response.text}")
        except:
            pass
        return

    # 2. Poll Status
    print("\nPolling status...")
    status_url = f"{BASE_URL}/api/unified/jobs/{job_id}"
    
    for i in range(30): # Poll for 60 seconds
        try:
            res = requests.get(status_url)
            res.raise_for_status()
            status_data = res.json()
            
            research_status = status_data.get("research", {}).get("status")
            guide_status = status_data.get("guide", {}).get("status")
            char_status = status_data.get("character", {}).get("status")
            
            print(f"[{i}] Research: {research_status}, Guide: {guide_status}, Char: {char_status}")
            
            if (research_status == "completed" or research_status == "COMPLETED") and \
               (guide_status == "COMPLETED") and \
               (char_status == "COMPLETED"):
                print("\nALL TASKS COMPLETED!")
                print(json.dumps(status_data, indent=2, ensure_ascii=False))
                break
            
            if research_status == "failed" or research_status == "FAILED":
               print("\nResearch FAILED!")
               print(f"Error: {status_data.get('research', {}).get('error')}")
               print(json.dumps(status_data, indent=2, ensure_ascii=False))
               break
                
            time.sleep(2)
        except Exception as e:
            print(f"Polling failed: {e}")
            break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Create a dummy image if none provided
        dummy_path = "test_seed.png"
        dummy_path = "test_seed.png"
        if not os.path.exists(dummy_path):
            import base64
            # 10x10 red pixel PNG (slightly larger)
            # data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
            # Let's generate a proper 100x100 png using python script if this fails, but let's try a simple 10x10 first or just use a known good base64
            # detailed 100x100 red square
            # Actually, let's just write a small python script to generate it using pure python struct pack if PIL is not there, 
            # OR just assume the user has a real image. 
            # But for automation, let's try to make a valid small png.
            
            # 1x1 is too small. Let's try 64x64.
            # I'll just use a python one-liner to create it if PIL is missing, but wait, I can't restart the script easily.
            # I will just put a larger base64 here.
            
            # Simple 1x1 was: iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg== 
            # (It is valid PNG but maybe too small for Gemini?)
            
            print("Creating dummy PNG (requires valid content)...")
            # If 1x1 failed, I'll try to download again or just mock the server response? No I need end to end.
            # I'll try to download using python requests since curl failed (maybe proxy issue?)
            
            try:
                import requests
                url = "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"
                r = requests.get(url)
                if r.status_code == 200:
                    with open(dummy_path, "wb") as f:
                        f.write(r.content)
                    print(f"Downloaded Google Logo to {dummy_path}")
                else:
                    raise Exception("Failed download")
            except:
                print("Download failed, using 1x1 fallback")
                data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
                with open(dummy_path, "wb") as f:
                    f.write(data)
                    
        test_unified_flow(dummy_path)
    else:
        test_unified_flow(sys.argv[1])
