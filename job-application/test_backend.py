import asyncio
import websockets
import os

# --- Configuration ---
# You can set the token as an environment variable or paste it directly here
CLERK_TOKEN = os.environ.get("CLERK_TEST_TOKEN", "your-clerk-jwt-token")
WEBSOCKET_URL = "ws://127.0.0.1:8000/ws/orchestrator"

async def test_orchestrator_ws():
    """
    Connects to the orchestrator WebSocket, sends a message, and prints the response.
    """
    uri = f"{WEBSOCKET_URL}?token={CLERK_TOKEN}"
    
    print(f"Connecting to {WEBSOCKET_URL}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Successfully connected to WebSocket.")
            
            # Send a test message
            message_to_send = "Hello, orchestrator! What are the top 3 tech jobs in San Francisco?"
            print(f"> Sending message: {message_to_send}")
            await websocket.send(message_to_send)
            
            # Wait for and print the response
            response = await websocket.recv()
            print(f"< Received response: {response}")

            # You can add more interactions here if needed
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e.reason} (code: {e.code})")
        if e.code == 1008:
            print("\n[Authentication Error]: The connection was closed with code 1008, which often means the token is invalid or expired. Please check the following:")
            print("1. Your FastAPI server is running.")
            print("2. The CLERK_SECRET_KEY is correctly set in your backend environment.")
            print("3. The token you provided is a valid, non-expired Clerk JWT for your application.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if CLERK_TOKEN == "your-clerk-jwt-token":
        print("="*50)
        print("WARNING: Please replace 'your-clerk-jwt-token' with a real Clerk JWT.")
        print("You can get a token from your frontend after a user logs in.")
        print("You can also set the CLERK_TEST_TOKEN environment variable.")
        print("="*50)
    else:
        asyncio.run(test_orchestrator_ws()) 