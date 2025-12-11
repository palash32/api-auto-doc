"""Direct import test of the settings."""
import sys
sys.path.insert(0, '.')

from app.core.config import settings

print("🔍 Settings object check:")
print(f"   GITHUB_WEBHOOK_SECRET value: {settings.GITHUB_WEBHOOK_SECRET}")
print(f"   Type: {type(settings.GITHUB_WEBHOOK_SECRET)}")
print(f"   Is None: {settings.GITHUB_WEBHOOK_SECRET is None}")
print(f"   Bool value: {bool(settings.GITHUB_WEBHOOK_SECRET)}")

if settings.GITHUB_WEBHOOK_SECRET:
    print(f"   ✅ Secret is loaded: {settings.GITHUB_WEBHOOK_SECRET[:15]}...")
else:
    print(f"   ❌ Secret is NOT loaded (value is falsy)")
