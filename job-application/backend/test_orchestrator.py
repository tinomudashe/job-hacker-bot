import asyncio
import websockets
import json

# --- Configuration ---
# Make sure to replace this with a fresh, valid token before running.
TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ii1sX0llanRjajJZRDRORi0ybjhpbSJ9.eyJpc3MiOiJodHRwczovL2Rldi1qdG1hOG9zdzY2dW01YnF1LnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJobWNSQ3QzZjM1REpDMk5GMGlWaXB3Z3J1YjFqbGdUU0BjbGllbnRzIiwiYXVkIjoiaHR0cHM6Ly9kZXYtanRtYThvc3c2NnVtNWJxdS51cy5hdXRoMC5jb20vYXBpL3YyLyIsImlhdCI6MTc0OTY0NjgwMywiZXhwIjoxNzQ5NzMzMjAzLCJndHkiOiJjbGllbnQtY3JlZGVudGlhbHMiLCJhenAiOiJobWNSQ3QzZjM1REpDMk5GMGlWaXB3Z3J1YjFqbGdUUyJ9.VlmQZZV7se17l_VQ0e7Ngf0qSlMLWja2LhLhCcFJUntOqFrbIVhOu2E_bjLEpDVRihYHECmX1lFuy3fHq_-NxPwJEr7t19g1SzBbBEoSoQs-OL22_JmqWyXXq65_I3F5XtTOEmNSJal9wmxtrm9viEXZtDQbolpBvE-ZaY38MuuhgApuc_cZRo68bdJeFsBWR1bqshpxHhbhZlbQpVzgQQJ5YG6tC0TqyLT8TpO8OJei9qQZaB5XzJeCI0vhNJFYvtdacq5SA3wp_ndLYxXulA18oVVkqgmGWqDzk3O6X3sqQA_2HszcATTO3Gfa-hdYwKUIrcpJ9-fo2_w_0gBEUQ"
URI = f"ws://127.0.0.1:8001/api/ws/orchestrator?token={TOKEN}"

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