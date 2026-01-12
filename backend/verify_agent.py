import os
import sys

# Ensure backend dir is in path to import agent
sys.path.append(os.path.dirname(__file__))

from agent import create_session, query_session

if __name__ == "__main__":
    if not os.environ.get("AGENT_ENDPOINT"):
        print("Please set AGENT_ENDPOINT environment variable.")
        sys.exit(1)

    print("Creating session...")
    try:
        session_name = create_session()
        print(f"Session created: {session_name}")
        
        # Turn 1
        q1 = "東京の天気は？"
        print(f"\nUser: {q1}")
        a1 = query_session(session_name, q1)
        print(f"Agent: {a1}")
        
        # Turn 2 (Context dependent)
        q2 = "大阪は？"
        print(f"\nUser: {q2}")
        a2 = query_session(session_name, q2)
        print(f"Agent: {a2}")
        
    except Exception as e:
        print(f"Error: {e}")
