"""Diagnostic script to test config loading"""
import os
import sys

print("=" * 50)
print("DIAGNOSTIC: Testing Configuration Loading")
print("=" * 50)

# Test 1: Check .env file exists
env_path = ".env"
print(f"\n1. .env file exists: {os.path.exists(env_path)}")

# Test 2: Load with python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("2. python-dotenv load: ✅ SUCCESS")
    print(f"   - DATABASE_URL: {bool(os.getenv('DATABASE_URL'))}")
    print(f"   - GEMINI_API_KEY: {bool(os.getenv('GEMINI_API_KEY'))}")
except Exception as e:
    print(f"2. python-dotenv load: ❌ FAILED - {e}")
    sys.exit(1)

# Test 3: Load pydantic BaseSettings
try:
    from pydantic_settings import BaseSettings
    
    class TestSettings(BaseSettings):
        DATABASE_URL: str = "test"
        GEMINI_API_KEY: str = ""
        
        class Config:
            env_file = ".env"
            extra = "ignore"
    
    test_settings = TestSettings()
    print("3. pydantic BaseSettings (old style): ✅ SUCCESS")
except Exception as e:
    print(f"3. pydantic BaseSettings (old style): ❌ FAILED - {e}")

# Test 4: Load with new pydantic-settings style
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict  
    
    class TestSettings2(BaseSettings):
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore"
        )
        
        DATABASE_URL: str = "test"
        GEMINI_API_KEY: str = ""
    
    test_settings2 = TestSettings2()
    print("4. pydantic SettingsConfigDict: ✅ SUCCESS")
except Exception as e:
    print(f"4. pydantic SettingsConfigDict: ❌ FAILED")
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Try loading actual app config
try:
    from app.core.config import settings
    print("5. app.core.config.settings: ✅ SUCCESS")
    print(f"   - Environment: {settings.ENVIRONMENT}")
    print(f"   - Database URL set: {bool(settings.DATABASE_URL)}")
    print(f"   - Gemini API Key set: {bool(settings.GEMINI_API_KEY)}")
except Exception as e:
    print(f"5. app.core.config.settings: ❌ FAILED")
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("DIAGNOSTIC COMPLETE")
print("=" * 50)
