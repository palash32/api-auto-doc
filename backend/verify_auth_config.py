import sys
import os
from dotenv import load_dotenv

def check_auth_config():
    print("🔍 Verifying Auth Configuration...")
    
    # Load .env
    load_dotenv()
    if not os.getenv("GOOGLE_CLIENT_ID"):
        # Try parent directory
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
        
    google_id = os.getenv("GOOGLE_CLIENT_ID")
    google_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    if not google_id:
        print("❌ GOOGLE_CLIENT_ID is missing")
        return False
        
    if not google_secret:
        print("❌ GOOGLE_CLIENT_SECRET is missing")
        return False
        
    if google_id == "your-client-id":
        print("❌ GOOGLE_CLIENT_ID is set to default placeholder")
        return False
        
    print(f"✅ GOOGLE_CLIENT_ID found: {google_id[:5]}...")
    print("✅ GOOGLE_CLIENT_SECRET found")
    
    print("\n✨ Auth configuration looks good!")
    return True

if __name__ == "__main__":
    if check_auth_config():
        sys.exit(0)
    else:
        sys.exit(1)
