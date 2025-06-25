import sys
from jose import jwt
import json

def decode_token_issuer(token: str):
    """
    Decodes a JWT without verifying its signature and prints the 'iss' claim.
    """
    try:
        # We decode without a key to inspect the payload, as signature verification
        # is handled by the server. This is just for inspection.
        decoded_payload = jwt.decode(token, "unused-key", options={"verify_signature": False})
        issuer = decoded_payload.get("iss")

        print("\n" + "="*50)
        print("JWT DECODING RESULT")
        print("="*50)

        if issuer:
            print(f"\n[SUCCESS] Issuer (iss) found in token:")
            print(f"  -> {issuer}")
            print("\nACTION: Please ensure your CLERK_ISSUER_URL in the .env file matches this value EXACTLY.")
        else:
            print("\n[ERROR] 'iss' claim not found in the token payload.")
            print("\nFull Decoded Payload:")
            print(json.dumps(decoded_payload, indent=2))
        
        print("\n" + "="*50)

    except Exception as e:
        print(f"\n[CRITICAL ERROR] An error occurred while decoding the token: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        jwt_token = sys.argv[1]
        decode_token_issuer(jwt_token)
    else:
        print("\nUsage: python debug_token.py <your-jwt-token>")
        print("Please provide the JWT token from your frontend as a command-line argument.") 