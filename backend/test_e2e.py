"""End-to-end test — exercises the full pipeline via API."""
import os
import sys
import uuid

# Force mock LLM provider for deterministic end-to-end testing
os.environ["LLM_PROVIDER"] = "mock"

from fastapi.testclient import TestClient
from main import app

BASE = "/api"

def test():
    with TestClient(app) as c:
        # 1. Register with unique email to ensure idempotence
        unique_email = f"test_{uuid.uuid4().hex[:8]}@aifre.com"
        print(f"1. Register user ({unique_email})...")
        r = c.post(f"{BASE}/auth/register", json={"email": unique_email, "password": "TestPassword123!", "full_name": "Senior Test Analyst", "role": "business_analyst"})
        assert r.status_code == 200, f"Register failed: {r.text}"
        data = r.json()
        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"   OK - User: {data['user']['full_name']} ({data['user']['role']})")

        # 2. Create project
        print("2. Create project...")
        r = c.post(f"{BASE}/projects", json={"name": "Digital Lending Suite", "description": "Automated lending platform with KYC/AML compliance", "use_case": "loan_processing"}, headers=headers)
        assert r.status_code == 200, f"Create project failed: {r.text}"
        project = r.json()
        pid = project["id"]
        print(f"   OK - Project: {project['name']} (ID: {pid[:8]}...) Stage: {project.get('current_stage')}")

        # 3. Start interview
        print("3. Start interview...")
        r = c.post(f"{BASE}/projects/{pid}/interview/start?stakeholder_role=business_analyst", headers=headers)
        assert r.status_code == 200, f"Interview start failed: {r.text}"
        interview = r.json()
        print(f"   OK - Question: {interview.get('question', '')[:80]}...")

        # 4. Answer interview
        print("4. Answer interview question...")
        r = c.post(f"{BASE}/projects/{pid}/interview/answer?answer=We+require+strict+KYC+verification+using+government+ID+and+biometrics.+The+system+must+compute+credit+scores+within+30+seconds.+All+PII+records+must+be+encrypted+with+AES-256.+The+platform+needs+to+sustain+500+concurrent+users+with+under+3+seconds+response+time.+All+audit+records+must+be+stored+for+7+years.", headers=headers)
        assert r.status_code == 200, f"Interview answer failed: {r.text}"
        answer = r.json()
        print(f"   OK - Follow-up: {answer.get('question', '')[:80]}...")

        # 5. Extract requirements
        print("5. Extract requirements from interview conversation...")
        r = c.post(f"{BASE}/projects/{pid}/requirements/extract", headers=headers)
        assert r.status_code == 200, f"Extraction failed: {r.text}"
        extraction = r.json()
        reqs = extraction.get("requirements", [])
        assert len(reqs) > 0, "No requirements extracted"
        print(f"   OK - Extracted {len(reqs)} requirements. First: {reqs[0].get('requirement_id')} - {reqs[0].get('statement')[:60]}...")

        # 6. Run analysis pipeline
        print("6. Run 7-stage analysis pipeline...")
        r = c.post(f"{BASE}/projects/{pid}/requirements/analyse", headers=headers)
        assert r.status_code == 200, f"Analysis failed: {r.text}"
        analysis = r.json()
        stages = list(analysis.keys())
        assert "clarification" in stages and "compliance" in stages and "security" in stages
        print(f"   OK - Stages completed: {', '.join(stages)}")
        print(f"   Security total analyzed: {analysis['security'].get('total_analysed', 0)}")
        print(f"   Compliance gaps analyzed: {len(analysis['compliance'].get('compliance_analysis', []))}")

        # 7. SDLC analysis
        print("7. Run SDLC analysis...")
        r = c.post(f"{BASE}/projects/{pid}/sdlc/analyse", headers=headers)
        assert r.status_code == 200, f"SDLC failed: {r.text}"
        sdlc = r.json()
        print(f"   OK - Recommended: {sdlc.get('display_name')} (score: {sdlc.get('recommended_score')})")
        print(f"   Scores: {sdlc.get('scores')}")

        # 8. Generate IEEE 29148 SRS Document (PDF & DOCX)
        print("8. Generate IEEE 29148 SRS Document...")
        r = c.post(f"{BASE}/projects/{pid}/srs/generate", headers=headers)
        assert r.status_code == 200, f"SRS generation failed: {r.text}"
        srs = r.json()
        print(f"   OK - Title: {srs.get('title')}")
        print(f"   PDF generated: {srs.get('pdf_filename')}")
        print(f"   DOCX generated: {srs.get('docx_filename')}")

        # 9. Preview SRS
        print("9. Preview SRS data structure...")
        r = c.get(f"{BASE}/projects/{pid}/srs/preview", headers=headers)
        assert r.status_code == 200, f"SRS preview failed: {r.text}"
        srs_preview = r.json()
        assert "srs_data" in srs_preview or "sections" in srs_preview
        print("   OK - SRS preview verified")

        # 10. Approvals workflow
        print("10. Check and action pending approvals...")
        r = c.get(f"{BASE}/projects/{pid}/approvals", headers=headers)
        assert r.status_code == 200, f"Approvals fetch failed: {r.text}"
        approvals = r.json()
        assert len(approvals) > 0, "No pending approvals found"
        app_id = approvals[0]["id"]
        print(f"   Found approval request: {approvals[0].get('title')} (Status: {approvals[0].get('status')})")

        # Action approval
        r = c.post(f"{BASE}/projects/{pid}/approvals/{app_id}/action", json={"action": "approve", "comments": "Requirements baseline verified against IEEE 29148 standards and KYC directives."}, headers=headers)
        assert r.status_code == 200, f"Approval action failed: {r.text}"
        print(f"   OK - Approved by {r.json().get('reviewer')}")

        # 11. Get audit trail
        print("11. Get audit trail...")
        r = c.get(f"{BASE}/projects/{pid}/audit-trail", headers=headers)
        assert r.status_code == 200, f"Audit trail failed: {r.text}"
        audit = r.json()
        assert len(audit) > 0, "Audit trail is empty"
        print(f"   OK - {len(audit)} audit entries recorded")

        # 12. Get session state
        print("12. Verify persistent session state...")
        r = c.get(f"{BASE}/projects/{pid}/session", headers=headers)
        assert r.status_code == 200, f"Session state failed: {r.text}"
        session = r.json()
        print(f"   OK - Stage: {session.get('stage')}, Requirements: {session.get('requirement_count')}, Has SRS: {session.get('has_srs')}")

        # 13. Run evaluation framework
        print("13. Run evaluation framework...")
        r = c.post(f"{BASE}/evaluation/run")
        assert r.status_code == 200, f"Evaluation failed: {r.text}"
        eval_data = r.json()
        metrics = eval_data.get("metrics", {})
        print(f"   OK - {metrics.get('total_test_cases', 0)} test cases, {metrics.get('passed_test_cases', 0)} passed")
        print(f"   Precision: {metrics.get('precision', 0):.2f}, F1: {metrics.get('f1', 0):.2f}")

        print("\n" + "="*60)
        print("[PASS] ALL 13 END-TO-END TESTS PASSED SUCCESSFULLY")
        print("="*60)

if __name__ == "__main__":
    try:
        test()
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        sys.exit(1)
