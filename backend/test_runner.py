"""Automated test runner for API endpoints."""

import asyncio
import httpx
from datetime import datetime
from typing import List, Dict, Any

BASE_URL = "http://localhost:8000"

# Test results
results: List[Dict[str, Any]] = []


async def test_endpoint(
    name: str,
    method: str,
    path: str,
    expected_status: int = 200,
    data: dict = None,
    headers: dict = None
):
    """Test a single endpoint."""
    url = f"{BASE_URL}{path}"
    start = datetime.now()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, json=data, headers=headers)
            elif method == "PATCH":
                response = await client.patch(url, json=data, headers=headers)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                response = await client.get(url, headers=headers)
        
        duration = (datetime.now() - start).total_seconds() * 1000
        passed = response.status_code == expected_status
        
        results.append({
            "name": name,
            "method": method,
            "path": path,
            "status": response.status_code,
            "expected": expected_status,
            "passed": passed,
            "duration_ms": round(duration, 2),
            "error": None
        })
        
        icon = "✅" if passed else "❌"
        print(f"{icon} {name}: {response.status_code} ({duration:.0f}ms)")
        
    except Exception as e:
        results.append({
            "name": name,
            "method": method,
            "path": path,
            "status": None,
            "expected": expected_status,
            "passed": False,
            "duration_ms": None,
            "error": str(e)
        })
        print(f"❌ {name}: ERROR - {e}")


async def run_tests():
    """Run all API tests."""
    print("\n" + "="*60)
    print("🧪 API Auto-Documentation Platform - Test Suite")
    print("="*60 + "\n")
    
    # ========== Health & Status ==========
    print("📡 Health & Status")
    print("-"*40)
    await test_endpoint("Health Dashboard", "GET", "/api/health/dashboard")
    await test_endpoint("Performance Dashboard", "GET", "/api/performance/dashboard")
    await test_endpoint("Queue Stats", "GET", "/api/performance/queue/stats")
    print()
    
    # ========== Auth (no token) ==========
    print("🔐 Authentication")
    print("-"*40)
    await test_endpoint("Auth Me (no token)", "GET", "/api/auth/me", expected_status=403)
    print()
    
    # ========== Repositories ==========
    print("📦 Repositories")
    print("-"*40)
    await test_endpoint("List Repositories", "GET", "/api/repositories/")
    print()
    
    # ========== Endpoints ==========
    # Note: /api/endpoints/{endpoint_id} requires a valid endpoint ID
    # Skipping this test as it needs seeded data
    print("🔗 Endpoints")
    print("-"*40)
    print("⚠️  Skipped: Requires endpoint ID")
    print()
    
    # ========== Billing ==========
    print("💳 Billing")
    print("-"*40)
    await test_endpoint("List Plans", "GET", "/api/billing/plans")
    await test_endpoint("Get Subscription", "GET", "/api/billing/subscription")
    await test_endpoint("List Invoices", "GET", "/api/billing/invoices")
    print()
    
    # ========== Search ==========
    print("🔍 Search")
    print("-"*40)
    await test_endpoint("Search Suggestions", "GET", "/api/search/suggestions")
    await test_endpoint("Saved Searches", "GET", "/api/search/saved")
    print()
    
    # ========== Analytics ==========
    print("📊 Analytics")
    print("-"*40)
    await test_endpoint("Top Endpoints", "GET", "/api/analytics/top-endpoints")
    print()
    
    # ========== Versions ==========
    print("📜 Versions")
    print("-"*40)
    await test_endpoint("Version Diff", "GET", "/api/versions/", expected_status=404)  # Requires version IDs
    print()
    
    # ========== Security ==========
    print("🔒 Security")
    print("-"*40)
    await test_endpoint("Audit Logs", "GET", "/api/security/audit-logs")
    await test_endpoint("SSO Config", "GET", "/api/security/sso")
    await test_endpoint("IP Whitelist", "GET", "/api/security/ip-whitelist")
    await test_endpoint("Security Settings", "GET", "/api/security/settings")
    await test_endpoint("API Keys", "GET", "/api/security/api-keys")
    print()
    
    # ========== Enterprise ==========
    print("🏢 Enterprise")
    print("-"*40)
    await test_endpoint("Enterprise Config", "GET", "/api/enterprise/config")
    await test_endpoint("Integrations", "GET", "/api/enterprise/integrations")
    await test_endpoint("Support Tickets", "GET", "/api/enterprise/tickets")
    await test_endpoint("SLA Metrics", "GET", "/api/enterprise/sla")
    print()
    
    # ========== CI/CD ==========
    print("🔄 CI/CD")
    print("-"*40)
    await test_endpoint("Pipelines", "GET", "/api/cicd/pipelines")
    await test_endpoint("Builds", "GET", "/api/cicd/builds")
    print()
    
    # ========== Import/Export ==========
    print("📤 Import/Export")
    print("-"*40)
    await test_endpoint("Import Jobs", "GET", "/api/import/jobs")
    await test_endpoint("Export Jobs", "GET", "/api/export/jobs")
    print()
    
    # ========== Team ==========
    print("👥 Team")
    print("-"*40)
    await test_endpoint("Team Members", "GET", "/api/team/members")
    await test_endpoint("Workspaces", "GET", "/api/team/workspaces")
    print()
    
    # ========== Branding ==========
    print("🎨 Branding")
    print("-"*40)
    await test_endpoint("Branding Config", "GET", "/api/branding/branding")
    await test_endpoint("Custom Domains", "GET", "/api/branding/domains")
    await test_endpoint("Branding Templates", "GET", "/api/branding/templates")
    print()
    
    # ========== Summary ==========
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])
    total = len(results)
    
    print(f"\n✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {failed}/{total}")
    print(f"📊 Pass Rate: {(passed/total*100):.1f}%")
    
    if failed > 0:
        print("\n⚠️  Failed Tests:")
        for r in results:
            if not r["passed"]:
                error = r.get("error") or f"Expected {r['expected']}, got {r['status']}"
                print(f"   - {r['name']}: {error}")
    
    # Performance stats
    durations = [r["duration_ms"] for r in results if r["duration_ms"]]
    if durations:
        avg = sum(durations) / len(durations)
        max_d = max(durations)
        print(f"\n⚡ Avg Response: {avg:.0f}ms")
        print(f"⚡ Max Response: {max_d:.0f}ms")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_tests())
