import sys

def check_import(module_name, package_name=None):
    if package_name is None:
        package_name = module_name
    try:
        __import__(module_name)
        print(f"✅ {package_name} imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import {package_name}: {e}")
        return False

print("🔍 Verifying Critical Dependencies...")
success = True
success &= check_import("fastapi", "FastAPI")
success &= check_import("pydantic", "Pydantic")
success &= check_import("sqlalchemy", "SQLAlchemy")
success &= check_import("google.generativeai", "Google Generative AI")

if success:
    print("\n✨ All critical dependencies are installed and working!")
    sys.exit(0)
else:
    print("\n⚠️ Some dependencies are missing or broken. Please run 'pip install -r requirements.txt'")
    sys.exit(1)
