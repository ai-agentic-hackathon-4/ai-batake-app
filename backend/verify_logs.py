import sys
import os
import asyncio

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import get_agent_execution_logs
from main import app
from fastapi.testclient import TestClient

def test_db_function():
    print("Testing get_agent_execution_logs from db.py...")
    try:
        logs = get_agent_execution_logs(limit=5)
        print(f"Successfully fetched {len(logs)} logs.")
        for log in logs:
            print(f" - Log: {log}")
    except Exception as e:
        print(f"Error calling db function: {e}")

def test_api_endpoint():
    print("\nTesting /api/agent-logs endpoint...")
    client = TestClient(app)
    try:
        response = client.get("/api/agent-logs")
        if response.status_code == 200:
            data = response.json()
            print(f"API Success: {len(data.get('logs', []))} logs returned.")
        else:
            print(f"API Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error calling API: {e}")

if __name__ == "__main__":
    test_db_function()
    test_api_endpoint()
