"""Check all loaded environment variables related to GitHub."""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print("🔍 Checking .env file loading:")
print(f"   .env file exists: {os.path.exists('.env')}")
print()

print("📋 GitHub-related environment variables:")
for key in os.environ.keys():
    if 'GITHUB' in key or 'WEBHOOK' in key:
        value = os.environ[key]
        if len(value) > 20:
            print(f"   {key} = {value[:20]}... ({len(value)} chars)")
        else:
            print(f"   {key} = {value}")

if not any('WEBHOOK' in k for k in os.environ.keys()):
    print("   ⚠️  No WEBHOOK variables found!")
    print()
    print("💡 Please add this line to your backend/.env file:")
    print("   GITHUB_WEBHOOK_SECRET=my_super_secret_webhook_key_2025")
