import os
import requests
import google.auth
import google.auth.transport.requests
import logging

# Setup Cloud Logging
try:
    import google.cloud.logging
    client = google.cloud.logging.Client()
    client.setup_logging()
    logging.info("Cloud Logging setup successfully.")
except Exception as e:
    # Fallback to standard logging if authentication fails (e.g. local dev without credentials)
    print(f"Failed to setup Cloud Logging: {e}")
    logging.basicConfig(level=logging.INFO)

def get_auth_headers():
    """Retrieves the Authorization header with a valid Google ID token."""
    creds, project = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)
    return {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json"
    }

def get_agent_location_and_id():
    """Parses AGENT_ENDPOINT to get location and agent ID."""
    agent_resource_name = os.environ.get("AGENT_ENDPOINT")
    if not agent_resource_name:
        logging.error("AGENT_ENDPOINT environment variable is not set")
        raise ValueError("AGENT_ENDPOINT environment variable is not set")
    
    parts = agent_resource_name.split("/")
    if "locations" not in parts:
         logging.error(f"Invalid AGENT_ENDPOINT format: {agent_resource_name}")
         raise ValueError(f"Invalid AGENT_ENDPOINT format: {agent_resource_name}")
            
    location = parts[parts.index("locations") + 1]
    return location, agent_resource_name

def create_session() -> str:
    """Creates a new session in Vertex AI Agent Engine."""
    location, agent_id = get_agent_location_and_id()
    url = f"https://{location}-aiplatform.googleapis.com/v1beta1/{agent_id}/sessions"
    
    headers = get_auth_headers()
    payload = {} 
    
    logging.info(f"Creating session for agent: {agent_id}")
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    
    session_name = response.json().get("name")
    logging.info(f"Session created: {session_name}")
    return session_name

def query_session(session_name: str, query_text: str) -> str:
    """Queries an existing session."""
    location, _ = get_agent_location_and_id()
    url = f"https://{location}-aiplatform.googleapis.com/v1beta1/{session_name}:query"
    
    headers = get_auth_headers()
    payload = {
        "input": {
            "role": "user",
            "content": query_text
        }
    }
    
    logging.info(f"Sending query to session {session_name}: {query_text}", extra={"query_text": query_text})
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    
    result_json = response.json()
    
    if "output" in result_json:
        output = result_json["output"]
        logging.info(f"Received response from agent: {output}", extra={"agent_response": output})
        if isinstance(output, dict) and "content" in output:
            return output["content"]
        return str(output)
    
    logging.warning(f"Unexpected response format: {result_json}")
    return str(result_json)

def get_weather_from_agent(region: str) -> str:
    """
    Sends a request to the Vertex AI Agent Engine.
    Creates a NEW session for each request (stateless usage of stateful API).
    """
    try:
        session_name = create_session()
        return query_session(session_name, f"{region}の天気を教えてください。")
    except Exception as e:
        logging.error(f"Agent connection error: {e}", exc_info=True)
        return f"エージェント通信エラー: {str(e)}"

