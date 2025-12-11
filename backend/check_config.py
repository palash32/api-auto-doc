"""Debug webhook to see actual config values."""
from app.core.config import settings

print("🔍 Webhook Configuration Check:")
print(f"   GITHUB_WEBHOOK_SECRET is set: {bool(settings.GITHUB_WEBHOOK_SECRET)}")
if settings.GITHUB_WEBHOOK_SECRET:
    print(f"   Secret length: {len(settings.GITHUB_WEBHOOK_SECRET)} characters")
    print(f"   First 10 chars: {settings.GITHUB_WEBHOOK_SECRET[:10]}...")
else:
    print("   ⚠️  SECRET NOT SET - Signature verification will be SKIPPED!")
