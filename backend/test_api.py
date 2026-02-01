from fastapi.testclient import TestClient
from main import app
import os
import sys

# Add backend to path if running from backend dir or parent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

client = TestClient(app)

def test_register_seed():
    # Path to the generated image artifact
    # I need to know where generate_image saves it. 
    # Usually it's in the artifacts directory. I will try to find it or passing it as arg.
    # For now, I'll search for it or let the user/agent populate the path.
    # I'll use a placeholder or assume a standard location if I can't find it dynamically.
    
    # Actually, the agent will know the path after generation.
    # I will make this script accept a file path as argument.
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <image_path>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    
    print(f"Testing with image: {image_path}")
    
    with open(image_path, "rb") as f:
        files = {"file": ("seed_packet.png", f, "image/png")}
        response = client.post("/api/register-seed", files=files)
        
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("SUCCESS: Endpoint returned 200")
    else:
        print("FAILURE: Endpoint returned error")

if __name__ == "__main__":
    test_register_seed()
