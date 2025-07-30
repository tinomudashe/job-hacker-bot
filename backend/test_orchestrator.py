import asyncio
import websockets
import json
import pytest

# --- Configuration ---
# Make sure to replace this with a fresh, valid token before running.
TOKEN = "<YOUR_VALID_TOKEN>"  # ⚠️ IMPORTANT: Replace with a valid token
URI = f"ws://127.0.0.1:8001/api/ws/orchestrator?token={TOKEN}"

@pytest.mark.asyncio
async def test_resume_agent():
    """
    Connects to the orchestrator websocket, sends a message to add a work experience,
    and prints the agent's response.
    """
    try:
        async with websockets.connect(URI) as websocket:
            print("--- Connected to WebSocket ---")
            
            # 1. Send a message to the agent
            message = "Please add a work experience for the role of 'Senior AI Researcher' at 'Future Tech Inc.' from '2022 to Present'. The description is 'Led research and development of next-generation language models.'"
            print(f"> Sending message: {message}")
            await websocket.send(message)
            
            # 2. Wait for and print the response
            response = await websocket.recv()
            print(f"< Received response: {response}")

            # 3. Verify the data was saved by asking the agent to retrieve it (optional)
            # This part is commented out as it requires the agent to have a "get_resume" tool
            # verify_message = "What is my most recent work experience?"
            # print(f"> Sending verification: {verify_message}")
            # await websocket.send(verify_message)
            # verification_response = await websocket.recv()
            # print(f"< Received verification: {verification_response}")

    except websockets.exceptions.ConnectionClosed as e:
        print(f"--- WebSocket connection closed: {e.code} {e.reason} ---")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(test_resume_agent())

@pytest.mark.asyncio
async def test_empty_page_id_handling():
    """
    Tests that the orchestrator correctly handles an empty page_id
    without disconnecting the client or raising an unhandled exception.
    """
    try:
        async with websockets.connect(URI) as websocket:
            print("--- Connected to WebSocket for page_id test ---")

            # 1. Construct a message with an empty page_id
            message_payload = {
                "content": "This is a test message with an empty page_id.",
                "page_id": ""  # Explicitly send an empty string
            }
            message_str = json.dumps(message_payload)
            print(f"> Sending message with empty page_id: {message_str}")

            # 2. Send the message
            await websocket.send(message_str)

            # 3. Wait for a response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                print(f"< Received response: {response}")
                # The test passes if a response is received and no exception is raised
                assert response is not None
            except asyncio.TimeoutError:
                pytest.fail("Did not receive a response from the agent within the timeout period.")

            # 4. Ensure the connection is still open
            assert websocket.open

    except websockets.exceptions.ConnectionClosed as e:
        pytest.fail(f"WebSocket connection closed unexpectedly: {e.code} {e.reason}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred: {e}") 