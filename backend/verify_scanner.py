"""
Verification script for Repository Scanner (Task 1.3).
Tests GitService and RepositoryScanner using a local dummy repo.
"""
import asyncio
import shutil
import os
from pathlib import Path
from app.services.git_service import GitService
from app.services.scanner import RepositoryScanner
from app.core.config import settings

# Setup dummy repo for testing
TEST_REPO_NAME = "test_owner/test_repo"
TEST_DIR = Path("./temp_test_repos")

def setup_dummy_repo():
    """Create a fake repo structure for testing scanner."""
    repo_path = TEST_DIR / "test_owner_test_repo"
    if repo_path.exists():
        shutil.rmtree(repo_path)
    
    repo_path.mkdir(parents=True)
    
    # Create valid files
    (repo_path / "main.py").write_text("print('Hello')")
    (repo_path / "utils.js").write_text("console.log('Hello')")
    (repo_path / "README.md").write_text("# Test Repo")
    
    # Create ignored files
    (repo_path / "node_modules").mkdir()
    (repo_path / "node_modules" / "lib.js").write_text("ignored")
    (repo_path / ".git").mkdir()
    (repo_path / ".git" / "config").write_text("ignored")
    (repo_path / "image.png").write_text("ignored")
    
    return repo_path

async def verify_scanner():
    print("🚀 Starting Repository Scanner Verification...")
    
    # 1. Setup
    repo_path = setup_dummy_repo()
    print(f"✅ Created dummy repo at {repo_path}")
    
    # 2. Test Scanner
    print("\n🔍 Testing RepositoryScanner...")
    scanner = RepositoryScanner()
    files = scanner.scan_repository(repo_path)
    
    print(f"Found {len(files)} files:")
    for f in files:
        print(f" - {f['path']} ({f['language']})")
        
    # Validation
    paths = [f['path'] for f in files]
    assert "main.py" in paths
    assert "utils.js" in paths
    
    # Check Metadata
    main_py = next(f for f in files if f['path'] == "main.py")
    print(f"\nMetadata for main.py: {main_py.get('metadata')}")
    
    # Since main.py content is just "print('Hello')", it has no functions
    # Let's update main.py to have a function to test parser
    (repo_path / "api.py").write_text("""
def get_users():
    '''Returns all users'''
    return []

@app.get('/items')
def get_items():
    return []
""")
    
    print("\n🔍 Rescanning to test parser...")
    files = scanner.scan_repository(repo_path)
    api_py = next(f for f in files if f['path'] == "api.py")
    
    functions = api_py['metadata']['functions']
    print(f"Found functions: {[f['name'] for f in functions]}")
    
    assert len(functions) == 2
    assert "get_users" in [f['name'] for f in functions]
    assert "get_items" in [f['name'] for f in functions]
    
    # Check docstring
    get_users = next(f for f in functions if f['name'] == "get_users")
    assert get_users['docstring'] == "Returns all users"
    
    # Check decorator
    get_items = next(f for f in functions if f['name'] == "get_items")
    assert "@app.get('/items')" in get_items['decorators']
    
    print("✅ Scanner logic verified: Correctly extracted metadata.")
    
    # 3. Test GitService (Mocking clone to avoid network)
    print("\noctocat Testing GitService...")
    # We override storage path to our test dir
    git_service = GitService(storage_path=str(TEST_DIR))
    
    # Test cleanup
    git_service.delete_repository(TEST_REPO_NAME)
    if not repo_path.exists():
        print(f"✅ GitService.delete_repository worked")
    else:
        print(f"❌ GitService.delete_repository failed")

if __name__ == "__main__":
    # Ensure config points to test dir
    settings.REPO_STORAGE_PATH = str(TEST_DIR)
    asyncio.run(verify_scanner())
