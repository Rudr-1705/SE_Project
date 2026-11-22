"""Security, Cross-User Access, Token Revocation, Workflow, and Persistence Tests."""
import os
import sys
import uuid

# Ensure deterministic mock provider is set for these tests
os.environ["LLM_PROVIDER"] = "mock"

from fastapi.testclient import TestClient
from main import app

BASE = "/api"


def run_all_tests():
    print("\n" + "=" * 70)
    print("AIFRE TEST SUITE: SECURITY, OWNERSHIP, WORKFLOW & PERSISTENCE")
    print("=" * 70 + "\n")

    with TestClient(app) as client:
        # =====================================================================
        # 1. AUTHENTICATION SECURITY & ROLE ENFORCEMENT
        # =====================================================================
        print("1. Testing Public Registration Role Restrictions...")

        # 1a. Attempt to register as admin -> MUST FAIL (400)
        admin_email = f"attacker_{uuid.uuid4().hex[:6]}@domain.com"
        r = client.post(f"{BASE}/auth/register", json={
            "email": admin_email,
            "password": "Password123!",
            "full_name": "Privilege Escalation Attempt",
            "role": "admin"
        })
        assert r.status_code == 400, f"Admin registration should be forbidden! Got: {r.status_code}"
        assert "forbidden" in r.text.lower(), f"Expected forbidden message, got: {r.text}"
        print("   [PASS] Registration as 'admin' was properly rejected with 400 Bad Request.")

        # 1b. Attempt to register as auditor -> MUST FAIL (400)
        r = client.post(f"{BASE}/auth/register", json={
            "email": f"auditor_{uuid.uuid4().hex[:6]}@domain.com",
            "password": "Password123!",
            "full_name": "Auditor Attempt",
            "role": "auditor"
        })
        assert r.status_code == 400, f"Auditor registration should be forbidden! Got: {r.status_code}"
        print("   [PASS] Registration as 'auditor' was properly rejected with 400 Bad Request.")

        # 1c. Register valid User A (Business Analyst)
        user_a_email = f"user_a_{uuid.uuid4().hex[:6]}@bank.com"
        r_a = client.post(f"{BASE}/auth/register", json={
            "email": user_a_email,
            "password": "Password123!",
            "full_name": "Alice Analyst",
            "role": "business_analyst"
        })
        assert r_a.status_code == 200, f"User A registration failed: {r_a.text}"
        user_a_token = r_a.json()["access_token"]
        user_a_id = r_a.json()["user"]["id"]
        headers_a = {"Authorization": f"Bearer {user_a_token}"}
        print(f"   [PASS] User A registered successfully as 'business_analyst' (ID: {user_a_id[:8]}).")

        # 1d. Register valid User B (Stakeholder)
        user_b_email = f"user_b_{uuid.uuid4().hex[:6]}@bank.com"
        r_b = client.post(f"{BASE}/auth/register", json={
            "email": user_b_email,
            "password": "Password123!",
            "full_name": "Bob Stakeholder",
            "role": "stakeholder"
        })
        assert r_b.status_code == 200, f"User B registration failed: {r_b.text}"
        user_b_token = r_b.json()["access_token"]
        user_b_id = r_b.json()["user"]["id"]
        headers_b = {"Authorization": f"Bearer {user_b_token}"}
        print(f"   [PASS] User B registered successfully as 'stakeholder' (ID: {user_b_id[:8]}).")

        # =====================================================================
        # 2. TOKEN REVOCATION & LOGOUT
        # =====================================================================
        print("\n2. Testing JWT Token Revocation on Logout...")

        # Create temporary User C to test revocation
        user_c_email = f"user_c_{uuid.uuid4().hex[:6]}@bank.com"
        r_c = client.post(f"{BASE}/auth/register", json={
            "email": user_c_email,
            "password": "Password123!",
            "full_name": "Charlie Revoke",
            "role": "business_analyst"
        })
        token_c = r_c.json()["access_token"]
        headers_c = {"Authorization": f"Bearer {token_c}"}

        # Verify token_c works for /me
        r_me = client.get(f"{BASE}/auth/me", headers=headers_c)
        assert r_me.status_code == 200, f"Token should be valid: {r_me.text}"
        print("   [PASS] Token authenticated before logout.")

        # Call logout
        r_logout = client.post(f"{BASE}/auth/logout", headers=headers_c)
        assert r_logout.status_code == 200, f"Logout failed: {r_logout.text}"
        print("   [PASS] Logout endpoint succeeded.")

        # Attempt to use revoked token_c -> MUST FAIL (401)
        r_revoked = client.get(f"{BASE}/auth/me", headers=headers_c)
        assert r_revoked.status_code == 401, f"Revoked token should return 401! Got: {r_revoked.status_code}"
        assert "revoked" in r_revoked.text.lower(), f"Expected revoked notice, got: {r_revoked.text}"
        print("   [PASS] Subsequent request using revoked token was blocked with 401 Unauthorized.")

        # =====================================================================
        # 3. PROJECT CREATION (USER A)
        # =====================================================================
        print("\n3. Testing Project Creation & Ownership Isolation...")
        r_proj = client.post(f"{BASE}/projects", json={
            "name": "Alpha Commercial Lending",
            "description": "Enterprise SME lending platform with biometric KYC and 30s credit scoring.",
            "use_case": "loan_processing",
            "jurisdiction": "US / Federal Reserve Guidelines"
        }, headers=headers_a)
        assert r_proj.status_code == 200, f"Create project failed: {r_proj.text}"
        proj_a = r_proj.json()
        proj_a_id = proj_a["id"]
        assert proj_a["owner_id"] == user_a_id
        assert proj_a["current_stage"] == "interview"
        print(f"   [PASS] Project created by User A (ID: {proj_a_id[:8]}, Stage: {proj_a['current_stage']}).")

        # =====================================================================
        # 4. CROSS-USER ACCESS CHECKS (USER B ATTEMPTS ACCESS TO USER A'S PROJECT)
        # =====================================================================
        print("\n4. Testing Cross-User Access Rejection on ALL Endpoints...")

        # 4a. Get project details
        r_cu = client.get(f"{BASE}/projects/{proj_a_id}", headers=headers_b)
        assert r_cu.status_code == 403, f"Expected 403, got {r_cu.status_code}"
        print("   [PASS] GET /projects/{id} -> 403 Forbidden")

        # 4b. Update project stage
        r_cu = client.put(f"{BASE}/projects/{proj_a_id}/stage", json={"stage": "analysis"}, headers=headers_b)
        assert r_cu.status_code == 403, f"Expected 403, got {r_cu.status_code}"
        print("   [PASS] PUT /projects/{id}/stage -> 403 Forbidden")

        # 4c. Start interview
        r_cu = client.post(f"{BASE}/projects/{proj_a_id}/interview/start", headers=headers_b)
        assert r_cu.status_code == 403, f"Expected 403, got {r_cu.status_code}"
        print("   [PASS] POST /interview/start -> 403 Forbidden")

        # 4d. Answer interview
        r_cu = client.post(f"{BASE}/projects/{proj_a_id}/interview/answer?answer=Hacked", headers=headers_b)
        assert r_cu.status_code == 403, f"Expected 403, got {r_cu.status_code}"
        print("   [PASS] POST /interview/answer -> 403 Forbidden")

        # 4e. Interview history
        r_cu = client.get(f"{BASE}/projects/{proj_a_id}/interview/history", headers=headers_b)
        assert r_cu.status_code == 403, f"Expected 403, got {r_cu.status_code}"
        print("   [PASS] GET /interview/history -> 403 Forbidden")

        # 4f. List requirements
        r_cu = client.get(f"{BASE}/projects/{proj_a_id}/requirements", headers=headers_b)
        assert r_cu.status_code == 403, f"Expected 403, got {r_cu.status_code}"
        print("   [PASS] GET /requirements -> 403 Forbidden")

        # 4g. Extract requirements
        r_cu = client.post(f"{BASE}/projects/{proj_a_id}/requirements/extract", headers=headers_b)
        assert r_cu.status_code == 403, f"Expected 403, got {r_cu.status_code}"
        print("   [PASS] POST /requirements/extract -> 403 Forbidden")

        # 4h. Run analysis
        r_cu = client.post(f"{BASE}/projects/{proj_a_id}/requirements/analyse", headers=headers_b)
        assert r_cu.status_code == 403, f"Expected 403, got {r_cu.status_code}"
        print("   [PASS] POST /requirements/analyse -> 403 Forbidden")

        # 4i. Run SDLC
        r_cu = client.post(f"{BASE}/projects/{proj_a_id}/sdlc/analyse", headers=headers_b)
        assert r_cu.status_code == 403, f"Expected 403, got {r_cu.status_code}"
        print("   [PASS] POST /sdlc/analyse -> 403 Forbidden")

        # 4j. Preview SRS
        r_cu = client.get(f"{BASE}/projects/{proj_a_id}/srs/preview", headers=headers_b)
        assert r_cu.status_code == 403, f"Expected 403, got {r_cu.status_code}"
        print("   [PASS] GET /srs/preview -> 403 Forbidden")

        # 4k. Download PDF
        r_cu = client.get(f"{BASE}/projects/{proj_a_id}/srs/download/pdf", headers=headers_b)
        assert r_cu.status_code == 403, f"Expected 403, got {r_cu.status_code}"
        print("   [PASS] GET /srs/download/pdf -> 403 Forbidden")

        # 4l. Download DOCX
        r_cu = client.get(f"{BASE}/projects/{proj_a_id}/srs/download/docx", headers=headers_b)
        assert r_cu.status_code == 403, f"Expected 403, got {r_cu.status_code}"
        print("   [PASS] GET /srs/download/docx -> 403 Forbidden")

        # 4m. Approvals list
        r_cu = client.get(f"{BASE}/projects/{proj_a_id}/approvals", headers=headers_b)
        assert r_cu.status_code == 403, f"Expected 403, got {r_cu.status_code}"
        print("   [PASS] GET /approvals -> 403 Forbidden")

        # 4n. Audit trail
        r_cu = client.get(f"{BASE}/projects/{proj_a_id}/audit-trail", headers=headers_b)
        assert r_cu.status_code == 403, f"Expected 403, got {r_cu.status_code}"
        print("   [PASS] GET /audit-trail -> 403 Forbidden")

        # =====================================================================
        # 5. WORKFLOW STAGE TRANSITION ENFORCEMENT
        # =====================================================================
        print("\n5. Testing Workflow Stage Enforcement...")

        # Attempt to jump straight to 'completed' stage without completing interview/SRS/approval -> MUST FAIL (400)
        r_skip = client.put(f"{BASE}/projects/{proj_a_id}/stage", json={"stage": "completed"}, headers=headers_a)
        assert r_skip.status_code == 400, f"Skipping to completed should fail! Got: {r_skip.status_code}"
        print("   [PASS] Skipping to 'completed' stage blocked with 400 Bad Request.")

        # Attempt to jump to 'srs' stage before extracting requirements -> MUST FAIL (400)
        r_skip = client.put(f"{BASE}/projects/{proj_a_id}/stage", json={"stage": "srs"}, headers=headers_a)
        assert r_skip.status_code == 400, f"Skipping to srs should fail! Got: {r_skip.status_code}"
        print("   [PASS] Skipping to 'srs' without requirements blocked with 400 Bad Request.")

        # =====================================================================
        # 6. FULL LEGITIMATE WORKFLOW EXECUTION (USER A)
        # =====================================================================
        print("\n6. Executing Legitimate Requirements Pipeline (User A)...")

        # 6a. Start interview
        r = client.post(f"{BASE}/projects/{proj_a_id}/interview/start?stakeholder_role=business_analyst", headers=headers_a)
        assert r.status_code == 200, f"Interview start failed: {r.text}"
        print("   [PASS] Interview started.")

        # 6b. Submit realistic answer
        rich_answer = (
            "We require automated commercial loan origination with biometric KYC identity verification. "
            "Credit scoring decisions must compute within 30 seconds under 500 concurrent sessions. "
            "All borrower data must be encrypted with AES-256 at rest and TLS 1.3 in transit. "
            "All compliance audit trails must be retained for 7 years under Federal Reserve guidelines."
        )
        r = client.post(f"{BASE}/projects/{proj_a_id}/interview/answer?answer={rich_answer.replace(' ', '+')}", headers=headers_a)
        assert r.status_code == 200, f"Interview answer failed: {r.text}"
        print("   [PASS] Interview answer recorded and follow-up generated.")

        # 6c. Advance to extraction and extract requirements
        client.put(f"{BASE}/projects/{proj_a_id}/stage", json={"stage": "extraction"}, headers=headers_a)
        r = client.post(f"{BASE}/projects/{proj_a_id}/requirements/extract", headers=headers_a)
        assert r.status_code == 200, f"Extraction failed: {r.text}"
        reqs = r.json().get("requirements", [])
        assert len(reqs) > 0, "No requirements extracted"
        print(f"   [PASS] Extracted {len(reqs)} requirements.")

        # 6d. Advance to analysis and run 7 agents
        client.put(f"{BASE}/projects/{proj_a_id}/stage", json={"stage": "analysis"}, headers=headers_a)
        r = client.post(f"{BASE}/projects/{proj_a_id}/requirements/analyse", headers=headers_a)
        assert r.status_code == 200, f"Analysis failed: {r.text}"
        analysis_data = r.json()
        assert "clarification" in analysis_data
        assert "compliance" in analysis_data
        assert "security" in analysis_data
        print("   [PASS] 7-dimension analysis executed successfully.")

        # 6e. Run SDLC recommendation
        client.put(f"{BASE}/projects/{proj_a_id}/stage", json={"stage": "sdlc"}, headers=headers_a)
        r = client.post(f"{BASE}/projects/{proj_a_id}/sdlc/analyse", headers=headers_a)
        assert r.status_code == 200, f"SDLC failed: {r.text}"
        sdlc_res = r.json()
        print(f"   [PASS] SDLC recommendation produced: {sdlc_res.get('display_name')} (Score: {sdlc_res.get('recommended_score')}).")

        # 6f. Generate IEEE 29148 SRS Document (Prior to approval -> MUST BE DRAFT STATUS)
        client.put(f"{BASE}/projects/{proj_a_id}/stage", json={"stage": "srs"}, headers=headers_a)
        r = client.post(f"{BASE}/projects/{proj_a_id}/srs/generate", headers=headers_a)
        assert r.status_code == 200, f"SRS generation failed: {r.text}"
        srs_json = r.json()
        srs_meta = srs_json.get("srs_data", {}).get("metadata", {})
        assert "APPROVED" not in srs_meta.get("status", ""), f"Unapproved SRS must not show APPROVED! Got: {srs_meta.get('status')}"
        assert "DRAFT" in srs_meta.get("status", "").upper()
        print(f"   [PASS] SRS generated with correct pre-approval status: '{srs_meta.get('status')}'.")

        # 6g. Authenticated PDF Download
        r_pdf = client.get(f"{BASE}/projects/{proj_a_id}/srs/download/pdf", headers=headers_a)
        assert r_pdf.status_code == 200, f"PDF download failed: {r_pdf.status_code}"
        assert r_pdf.content.startswith(b"%PDF-"), "Invalid PDF binary header!"
        print(f"   [PASS] Downloaded PDF verified with valid %PDF- header ({len(r_pdf.content)} bytes).")

        # 6h. Authenticated DOCX Download
        r_docx = client.get(f"{BASE}/projects/{proj_a_id}/srs/download/docx", headers=headers_a)
        assert r_docx.status_code == 200, f"DOCX download failed: {r_docx.status_code}"
        assert r_docx.content.startswith(b"PK\x03\x04"), "Invalid DOCX zip binary header!"
        print(f"   [PASS] Downloaded DOCX verified with valid PK\\x03\\x04 header ({len(r_docx.content)} bytes).")

        # 6i. Advance to approval and action sign-off
        client.put(f"{BASE}/projects/{proj_a_id}/stage", json={"stage": "approval"}, headers=headers_a)
        r_apps = client.get(f"{BASE}/projects/{proj_a_id}/approvals", headers=headers_a)
        assert r_apps.status_code == 200, f"Approvals fetch failed: {r_apps.text}"
        apps = r_apps.json()
        assert len(apps) > 0, "No pending approval found"
        app_id = apps[0]["id"]

        r_act = client.post(f"{BASE}/projects/{proj_a_id}/approvals/{app_id}/action", json={
            "action": "approve",
            "comments": "Statutory KYC and IEEE 29148 requirements baseline verified and signed off."
        }, headers=headers_a)
        assert r_act.status_code == 200, f"Approval action failed: {r_act.text}"
        print(f"   [PASS] Approval sign-off executed by {r_act.json().get('reviewer')}.")

        # Check project is completed
        r_proj_final = client.get(f"{BASE}/projects/{proj_a_id}", headers=headers_a)
        assert r_proj_final.json()["current_stage"] == "completed"
        print("   [PASS] Project automatically transitioned to 'completed' stage.")

        # 6j. Post-approval SRS generation check -> MUST BE APPROVED BASELINE
        r_srs_post = client.get(f"{BASE}/projects/{proj_a_id}/srs/preview", headers=headers_a)
        srs_meta_post = r_srs_post.json().get("srs_data", {}).get("metadata", {})
        assert "APPROVED BASELINE" in srs_meta_post.get("status", "")
        print(f"   [PASS] Post-approval SRS status correctly updated to: '{srs_meta_post.get('status')}'.")

        # =====================================================================
        # 7. AUDIT LOG PERSISTENCE & DATABASE INTEGRITY
        # =====================================================================
        print("\n7. Verifying Persistent Database Audit Logs...")
        r_audit = client.get(f"{BASE}/projects/{proj_a_id}/audit-trail", headers=headers_a)
        assert r_audit.status_code == 200, f"Audit trail failed: {r_audit.text}"
        audit_records = r_audit.json()
        assert len(audit_records) >= 8, f"Expected persistent audit records, got {len(audit_records)}"
        actions = [a.get("action") for a in audit_records]
        assert "approve" in actions, "Approval action missing from audit trail"
        assert any("extract" in str(a) for a in actions), "Extraction action missing from audit trail"
        print(f"   [PASS] Verified {len(audit_records)} persistent audit records in SQLite database.")

        # =====================================================================
        # 8. STAGE REVISITING WITHOUT DATA LOSS
        # =====================================================================
        print("\n8. Testing Revisit Completed Stages Without Data Loss...")
        r_revisit = client.put(f"{BASE}/projects/{proj_a_id}/stage", json={"stage": "extraction"}, headers=headers_a)
        assert r_revisit.status_code == 200
        # Verify requirements are still there
        r_req_check = client.get(f"{BASE}/projects/{proj_a_id}/requirements", headers=headers_a)
        assert len(r_req_check.json()) == len(reqs)
        # Advance back to completed
        client.put(f"{BASE}/projects/{proj_a_id}/stage", json={"stage": "completed"}, headers=headers_a)
        print("   [PASS] User revisited 'extraction' stage; verified all requirements and data intact.")

    print("\n" + "=" * 70)
    print("ALL SECURITY, OWNERSHIP, WORKFLOW & PERSISTENCE TESTS PASSED [100%]")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        run_all_tests()
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
