import os
import requests
import google.auth
import google.auth.transport.requests
import logging
import json

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
    # Session creation payload
    # user_id is often required or good practice for tracking.
    payload = {
        "userId": "test-user"
    } 
    
    logging.info(f"Creating session for agent: {agent_id}")
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error(f"Failed to create session. Status: {response.status_code}, Body: {response.text}")
        raise ValueError(f"Session creation failed: {e}. Body: {response.text}") from e
    
    resp_json = response.json()
    operation_name = resp_json.get("name")
    
    # Check if it's a Long Running Operation
    if "/operations/" in operation_name:
        logging.info(f"Session creation returned LRO: {operation_name}. Waiting for completion...")
        return wait_for_lro(operation_name)
    
    # Immediate success (unlikely for this API but possible)
    logging.info(f"Session created immediately: {operation_name}")
    return operation_name

def wait_for_lro(operation_name: str) -> str:
    """Polls a Long Running Operation until it completes."""
    import time
    location, _ = get_agent_location_and_id()
    # Operation name is full resource path: projects/.../locations/.../operations/...
    # But we need to construct the URL. The operation_name usually starts with projects/
    base_url = f"https://{location}-aiplatform.googleapis.com/v1beta1"
    url = f"{base_url}/{operation_name}"
    
    headers = get_auth_headers()
    
    for _ in range(30): # Timeout after roughly 30-60 seconds
        logging.info(f"Polling LRO: {operation_name}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        op_json = response.json()
        if op_json.get("done"):
            if "error" in op_json:
                raise ValueError(f"LRO failed: {op_json['error']}")
            
            # Success! Extract the resource name from the 'response' field
            # The 'response' field contains the Session resource
            if "response" in op_json and "name" in op_json["response"]:
                session_name = op_json["response"]["name"]
                logging.info(f"LRO completed. Session created: {session_name}")
                return session_name
            else:
                logging.error(f"LRO completed but missing 'response.name': {op_json}")
                raise ValueError("LRO completed but returned invalid response format")
        
        time.sleep(2)
        
    raise TimeoutError(f"Timed out waiting for LRO: {operation_name}")

def query_session(session_name: str, query_text: str) -> str:
    """Queries an existing session."""
    location, agent_id = get_agent_location_and_id()
    # Use the Reasoning Engine streamQuery endpoint with SSE
    url = f"https://{location}-aiplatform.googleapis.com/v1beta1/{agent_id}:streamQuery?alt=sse"
    
    headers = get_auth_headers()
    
    # Based on official docs:
    # class_method must be "async_stream_query"
    # input keys: user_id, session_id, message
    # Note: user_id is required even if session exists? Docs say yes.
    # We use "test-user" as used in creation.
    # IMPORTANT: session_id must be the ID only, not the full resource name
    session_id_only = session_name.split("/")[-1]
    
    payload = {
        "class_method": "async_stream_query",
        "input": {
            "user_id": "test-user",
            "session_id": session_id_only,
            "message": query_text
        }
    }
    
    logging.info(f"Sending query to agent {agent_id} (session: {session_name}): {query_text}", extra={"query_text": query_text})
    logging.info(f"Sending query to agent {agent_id} (session: {session_name}): {query_text}", extra={"query_text": query_text})
    
    # Use stream=True for SSE
    response = requests.post(url, json=payload, headers=headers, stream=True, timeout=60)
    
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error(f"Failed to query session. Status: {response.status_code}, Body: {response.text}")
        raise ValueError(f"Query session failed: {e}. Body: {response.text}") from e
    
    combined_text = ""
    
    # Parse SSE stream
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8').strip()
            if not decoded_line:
                continue
                
            # Handle standard SSE "data: " prefix
            if decoded_line.startswith("data:"):
                json_str = decoded_line[5:].strip()
            else:
                # Handle raw NDJSON or other formats
                json_str = decoded_line
                
            try:
                # Skip simple "data: " keep-alives or empty data
                if not json_str:
                    continue
                    
                event_data = json.loads(json_str)
                
                # Extract text content from the complex event structure
                # Structure: {'author': '...', 'content': {'parts': [{'text': '...'}]}, ...}
                if "content" in event_data:
                    content = event_data["content"]
                    if "parts" in content and isinstance(content["parts"], list):
                        for part in content["parts"]:
                            if "text" in part:
                                combined_text += part["text"]
                    elif isinstance(content, str):
                            # Fallback if content is string
                            combined_text += content
                            
                
            except json.JSONDecodeError:
                logging.warning(f"Failed to decode stream line: {decoded_line}")
            except Exception as e:
                logging.warning(f"Error processing event data: {e} - {json_str}")

    if not combined_text:
         logging.warning("No text content received from stream.")
         # It's possible the agent returned function calls or other non-text parts?
         # For now, return empty string or specific message?
         # raise ValueError("Agent returned empty response")
    
    logging.info(f"Received response from agent: {combined_text}", extra={"agent_response": combined_text})
    return combined_text

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

