"""
Debug script to test the scanning pipeline locally.
Run: python debug_scanner.py
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
from app.services.git_service import GitService
from app.services.scanner import RepositoryScanner
from app.services.scan_service import ScanService

# Test repo - palash32's Blogging-App (has API endpoints)
TEST_REPO_URL = "https://github.com/palash32/Blogging-App"
TEST_REPO_NAME = "palash32/Blogging-App"

async def debug_pipeline():
    print("=" * 60)
    print("🔬 SCANNER DEBUG PIPELINE")
    print("=" * 60)

    # 1. Git Service - Clone
    print("\n📥 STEP 1: Cloning Repository...")
    git_service = GitService()
    try:
        repo_path = await git_service.clone_repository(TEST_REPO_URL, TEST_REPO_NAME)
        print(f"   ✅ Cloned to: {repo_path}")
    except Exception as e:
        print(f"   ❌ Clone failed: {e}")
        return

    # 2. Scanner - Find files
    print("\n📁 STEP 2: Scanning for files...")
    scanner = RepositoryScanner()
    files = scanner.scan_repository(repo_path)
    print(f"   ✅ Found {len(files)} total files")
    
    # Show breakdown by language
    by_lang = {}
    for f in files:
        lang = f.get("language", "unknown")
        by_lang[lang] = by_lang.get(lang, 0) + 1
    print(f"   📊 By language: {by_lang}")

    # 3. Filter code files
    print("\n🔍 STEP 3: Filtering to code files...")
    SUPPORTED = ["python", "javascript", "typescript", "go", "java", "csharp"]
    code_files = [f for f in files if f.get("language") in SUPPORTED]
    print(f"   ✅ Found {len(code_files)} code files")
    
    if len(code_files) == 0:
        print("   ❌ NO CODE FILES FOUND - this is the problem!")
        return
    
    # Show first 10 code files
    print("   📄 Sample code files:")
    for f in code_files[:10]:
        print(f"      - {f['path']} ({f['language']}, {f.get('size', 0)} bytes)")

    # 4. Load content
    print("\n📖 STEP 4: Loading file contents...")
    files_with_content = []
    for f in code_files[:20]:  # Limit to 20 for debug
        try:
            content = scanner.get_file_content(repo_path, f["path"])
            f["_content"] = content
            files_with_content.append(f)
            print(f"   ✅ Loaded: {f['path']} ({len(content)} chars)")
        except Exception as e:
            print(f"   ⚠️ Failed: {f['path']}: {e}")

    # 5. Extract endpoints using regex (from scan_service)
    print("\n🔎 STEP 5: Extracting endpoints with regex...")
    import re
    
    endpoints_found = []
    for f in files_with_content:
        content = f.get("_content", "")
        lang = f.get("language", "")
        
        # Python patterns
        if lang == "python":
            patterns = [
                (r'@(?:app|router|blueprint)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', "fastapi"),
                (r'@(?:app|blueprint)\.route\s*\(\s*["\']([^"\']+)["\']', "flask"),
            ]
        # JavaScript patterns
        elif lang in ["javascript", "typescript"]:
            patterns = [
                (r'(?:app|router)\s*\.\s*(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', "express"),
            ]
        else:
            patterns = []
        
        for pattern, framework in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if framework == "flask":
                    path = match  # Only path captured
                    method = "GET"
                else:
                    method, path = match[0].upper(), match[1] if len(match) > 1 else match[0]
                
                endpoints_found.append({
                    "path": path,
                    "method": method,
                    "file": f["path"],
                    "framework": framework
                })
                print(f"   ✨ Found: {method} {path} in {f['path']}")

    print(f"\n{'=' * 60}")
    print(f"📊 SUMMARY")
    print(f"{'=' * 60}")
    print(f"   Total files: {len(files)}")
    print(f"   Code files: {len(code_files)}")
    print(f"   Endpoints found: {len(endpoints_found)}")
    
    if len(endpoints_found) == 0:
        print("\n   ⚠️ NO ENDPOINTS DETECTED!")
        print("   Possible causes:")
        print("     1. Repo doesn't have standard API patterns")
        print("     2. Regex patterns don't match this repo's style")
        print("     3. Files are using non-standard framework")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    git_service.delete_repository(TEST_REPO_NAME)
    print("   ✅ Done")

if __name__ == "__main__":
    asyncio.run(debug_pipeline())
