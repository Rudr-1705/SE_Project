"""End-to-end test — exercises the full pipeline via API."""
import httpx
import json
import sys

BASE = "http://localhost:8000/api"

def test():
    c = httpx.Client(base_url=BASE, timeout=30)

    # 1. Register
    print("1. Register user...")
    r = c.post("/auth/register", json={"email": "test@aifre.com", "password": "test12345", "full_name": "Test User", "role": "admin"})
    assert r.status_code == 200, f"Register failed: {r.text}"
    data = r.json()
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"   OK — User: {data['user']['full_name']} ({data['user']['role']})")

    # 2. Create project
    print("2. Create project...")
    r = c.post("/projects", json={"name": "Loan Processing System", "description": "Digital loan platform", "use_case": "loan_processing"}, headers=headers)
    assert r.status_code == 200, f"Create project failed: {r.text}"
    project = r.json()
    pid = project["id"]
    print(f"   OK — Project: {project['name']} (ID: {pid[:8]}...)")

    # 3. Start interview
    print("3. Start interview...")
    r = c.post(f"/projects/{pid}/interview/start?stakeholder_role=business_analyst", headers=headers)
    assert r.status_code == 200, f"Interview start failed: {r.text}"
    interview = r.json()
    print(f"   OK — Question: {interview.get('question', '')[:80]}...")

    # 4. Answer interview
    print("4. Answer interview question...")
    r = c.post(f"/projects/{pid}/interview/answer?answer=We+need+a+loan+processing+system+that+handles+personal+and+mortgage+loans+with+KYC+verification+and+credit+scoring", headers=headers)
    assert r.status_code == 200, f"Interview answer failed: {r.text}"
    answer = r.json()
    print(f"   OK — Follow-up: {answer.get('question', '')[:80]}...")

    # 5. Extract requirements
    print("5. Extract requirements...")
    text = "The system must verify applicant identity using government ID. It must perform automated credit scoring. All data must be encrypted with AES-256. The system should handle 500 concurrent users with response times under 5 seconds."
    r = c.post(f"/projects/{pid}/requirements/extract?text={text}&source_type=conversation", headers=headers)
    assert r.status_code == 200, f"Extraction failed: {r.text}"
    extraction = r.json()
    reqs = extraction.get("requirements", [])
    print(f"   OK — Extracted {len(reqs)} requirements")

    # 6. Run analysis pipeline
    print("6. Run analysis pipeline...")
    r = c.post(f"/projects/{pid}/requirements/analyse", headers=headers)
    assert r.status_code == 200, f"Analysis failed: {r.text}"
    analysis = r.json()
    stages = list(analysis.keys())
    print(f"   OK — Stages completed: {', '.join(stages)}")

    # 7. SDLC analysis
    print("7. Run SDLC analysis...")
    r = c.post(f"/projects/{pid}/sdlc/analyse", headers=headers)
    assert r.status_code == 200, f"SDLC failed: {r.text}"
    sdlc = r.json()
    print(f"   OK — Recommended: {sdlc.get('display_name', sdlc.get('recommended_model', '?'))} (score: {sdlc.get('recommended_score', '?')})")

    # 8. Generate SRS
    print("8. Generate SRS artefact...")
    r = c.post(f"/projects/{pid}/artefacts/generate?artefact_type=srs&project_name=Loan+Processing", headers=headers)
    assert r.status_code == 200, f"SRS generation failed: {r.text}"
    srs = r.json()
    print(f"   OK — Title: {srs.get('title', '?')}")

    # 9. Generate user stories
    print("9. Generate user stories...")
    r = c.post(f"/projects/{pid}/artefacts/generate?artefact_type=user_stories&project_name=Loan+Processing", headers=headers)
    assert r.status_code == 200, f"User stories failed: {r.text}"
    print(f"   OK — Generated user stories artefact")

    # 10. Get audit trail
    print("10. Get audit trail...")
    r = c.get(f"/projects/{pid}/audit-trail", headers=headers)
    assert r.status_code == 200, f"Audit trail failed: {r.text}"
    audit = r.json()
    print(f"   OK — {len(audit)} audit entries")

    # 11. Get session state
    print("11. Get session state...")
    r = c.get(f"/projects/{pid}/session", headers=headers)
    assert r.status_code == 200, f"Session state failed: {r.text}"
    session = r.json()
    print(f"   OK — Stage: {session.get('stage')}, Requirements: {session.get('requirement_count')}")

    # 12. Run evaluation
    print("12. Run evaluation framework...")
    r = c.post("/evaluation/run")
    assert r.status_code == 200, f"Evaluation failed: {r.text}"
    eval_data = r.json()
    metrics = eval_data.get("metrics", {})
    print(f"   OK — {metrics.get('total_test_cases', 0)} test cases, {metrics.get('passed_test_cases', 0)} passed")
    print(f"   Precision: {metrics.get('precision', 0):.2f}, F1: {metrics.get('f1', 0):.2f}")

    print("\n" + "="*60)
    print("[PASS] ALL 12 END-TO-END TESTS PASSED")
    print("="*60)

if __name__ == "__main__":
    try:
        test()
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        sys.exit(1)
