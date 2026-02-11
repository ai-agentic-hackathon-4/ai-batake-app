#!/usr/bin/env python3
"""
Test script for agent log comment integration.
Verifies that the character message endpoint correctly retrieves comments from agent_execution_logs.
"""
import requests
import json

BASE_URL = "http://localhost:8081"

def test_agent_logs():
    """Test the /api/agent-logs endpoint"""
    print("=" * 60)
    print("1. Testing /api/agent-logs endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/agent-logs", timeout=10)
        
        if response.status_code == 200:
            logs = response.json()
            print(f"✅ Found {len(logs)} agent logs")
            
            if logs:
                print("\n📝 Latest log structure:")
                latest = logs[0]
                print(json.dumps({
                    "timestamp": latest.get("timestamp", "N/A"),
                    "has_data_field": "data" in latest,
                    "has_comment": "data" in latest and "comment" in latest.get("data", {}),
                    "comment_preview": latest.get("data", {}).get("comment", "N/A")[:100] if "data" in latest else "N/A"
                }, indent=2, ensure_ascii=False))
            else:
                print("⚠️  No agent logs found in database")
        else:
            print(f"❌ HTTP {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()

def test_character_message():
    """Test the /api/character/message endpoint"""
    print("=" * 60)
    print("2. Testing /api/character/message endpoint")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/character/message", timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS - Response Data:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Check if message looks like it came from agent log or is fallback
            message = data.get('message', '')
            if '元気に育てていこうね' in message and 'こんにちは' in message:
                print("\n⚠️  Message appears to be fallback (no agent log comment found)")
            else:
                print("\n✅ Message appears to be from agent execution log")
                
        else:
            print(f"❌ FAILED - HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()

def main():
    print("\n🧪 Agent Log Comment Integration Test\n")
    test_agent_logs()
    test_character_message()
    print("=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
