import asyncio
import os
from app.services.ai_service import GeminiService
from app.core.config import settings

# Mock metadata for testing
TEST_METADATA = {
    "name": "create_user",
    "params": "(user: UserCreate, db: Session = Depends(get_db))",
    "docstring": "Register a new user in the system.",
    "decorators": ["@app.post('/users')", "@login_required"],
    "start_line": 10,
    "end_line": 15
}

async def verify_ai():
    print("🚀 Starting Gemini Verification...")
    
    if not settings.GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY is missing in .env")
        return
        
    service = GeminiService()
    print("✅ GeminiService initialized")
    
    print(f"\n📤 Sending prompt for: {TEST_METADATA['name']}...")
    result = await service.generate_documentation(TEST_METADATA)
    
    print("\n📥 Received Response:")
    print(result)
    
    # Validation
    if "error" in result:
        print(f"❌ AI Generation failed: {result['error']}")
        return

    assert "summary" in result
    assert "description" in result
    assert "tags" in result
    assert isinstance(result["tags"], list)
    
    print("\n✅ AI Logic verified: Returned valid JSON structure.")

if __name__ == "__main__":
    asyncio.run(verify_ai())
