import asyncio
import websockets
import json

# --- CONFIGURATION ---
# Your token has been added.
AUTH_TOKEN = "eyJhbGciOiJSUzI1NiIsImNhdCI6ImNsX0I3ZDRQRDExMUFBQSIsImtpZCI6Imluc18yeVZORXRXbXpyUFVZckswTDYzR2hJdElxeEsiLCJ0eXAiOiJKV1QifQ.eyJhenAiOiJodHRwOi8vbG9jYWxob3N0OjMwMDAiLCJleHAiOjE3NTE5MjM4MzcsImZ2YSI6WzQ4LC0xXSwiaWF0IjoxNzUxOTIzNzc3LCJpc3MiOiJodHRwczovL2NsZXZlci1lc2NhcmdvdC00Mi5jbGVyay5hY2NvdW50cy5kZXYiLCJuYmYiOjE3NTE5MjM3NjcsInNpZCI6InNlc3NfMnpZdldyVzI5M0gxZDhFVWZjMXNodkc1RXc4Iiwic3ViIjoidXNlcl8yeWF0RzRvTWdjUUNBeVlORnJlbkl4aWNWMUEiLCJ2IjoyfQ.CjfVgvmk6uUV5jV6jWc5i4zL73ozCvkzpJ4wkqqFQ02Z3UjMYxMDLpzkjO8PdTquCbMwSh2-KZGBhM_0PBT6W2KTGoeqyJhq8u0w72d9PBrDaH0-7aYqSDXa_N-_s3TH_7mmWDNQdFLEiFTtuAKFW_1Pd9Kttd9n30a01waFffxaqGQOEmxbhfeqVyYpfcZsep8gLUWldfv1cV0H5kfi-ApgirYRP5LcwoHtNTnbq_ATF5VCfqbeoSs703dvRR6SAMXZXaxV5-TJe3mkF1tU-ZbCfrAsPx1TFQAE85s9UzsaYTxTpLVabVRKCKZZRFdicJjxnPwJx56tEF4lJAyfg"

# This is the prompt that will be sent to the agent
PROMPT = "Write a cover letter for a Senior Software Engineer at a major tech company. I have 5 years of experience with Python and cloud technologies."

# You can get a page_id from your browser URL or leave it as a new one
PAGE_ID = "test_page_cl_12345"
# --- END CONFIGURATION ---

WEBSOCKET_URL = f"ws://localhost:8000/api/ws/orchestrator?token={AUTH_TOKEN}"

async def run_test():
    """Connects to the WebSocket, sends a message, and prints the response."""
    print(f"Connecting to {WEBSOCKET_URL}...")
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            print("Connection successful!")

            # This payload mimics the format sent by the frontend
            payload = {
                "type": "message",
                "content": PROMPT,
                "page_id": PAGE_ID
            }

            print(f"Sending message: {json.dumps(payload, indent=2)}")
            await websocket.send(json.dumps(payload))

            print("\nWaiting for agent's response...")
            
            # Listen for the response from the server
            response_str = await websocket.recv()
            response_json = json.loads(response_str)

            print("\n--- AGENT RESPONSE ---")
            print(json.dumps(response_json, indent=2))
            print("--- END RESPONSE ---\n")

            if "message" in response_json and "[DOWNLOADABLE_COVER_LETTER]" in response_json["message"]:
                print("✅ SUCCESS: The agent responded with the cover letter trigger.")
            else:
                print("❌ FAILED: The agent did not respond with the cover letter trigger.")

    except websockets.exceptions.ConnectionClosedError as e:
        print(f"\n❌ ERROR: Connection failed. Code: {e.code}, Reason: {e.reason}")
        if e.code == 1008:
            print("💡 TIP: The AUTH_TOKEN might be invalid or expired. Please get a new one from your browser.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Ensure you have the library installed: pip install websockets
    asyncio.run(run_test())