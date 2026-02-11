#!/usr/bin/env python3
"""
Test script for character message API endpoint.
"""
import requests
import json

BASE_URL = "http://localhost:8081"

def test_character_message_api():
    """Test the /api/character/message endpoint"""
    print("Testing /api/character/message endpoint...")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/character/message", timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS - Response Data:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print()
            
            # Verify expected fields
            expected_fields = ['character_name', 'message', 'avatar_url']
            missing_fields = [f for f in expected_fields if f not in data]
            
            if missing_fields:
                print(f"⚠️  WARNING: Missing fields: {missing_fields}")
            else:
                print("✅ All expected fields present")
                
            # Check message is not empty
            if data.get('message'):
                print(f"✅ Message generated: {data['message'][:100]}...")
            else:
                print("⚠️  WARNING: Message is empty")
                
        else:
            print(f"❌ FAILED - HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to backend")
        print("Please make sure the backend is running on port 8081")
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out")
        print("The AI message generation may be taking too long")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    print("=" * 60)

if __name__ == "__main__":
    print("Character Message API Test")
    print()
    test_character_message_api()
