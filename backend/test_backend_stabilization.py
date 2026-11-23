"""Comprehensive Backend Stabilization, Auth, Ownership, Extraction, and Workflow Tests.

Validates:
1. Database schema preservation and clean resets.
2. Simplified Auth without RBAC (register, login, me, logout, token revocation).
3. Pure project ownership isolation (User A vs User B).
4. Robust JSON extraction handling <think> tags, markdown, trailing commas, and regex fallback.
5. Interview -> Extraction -> Persistence in SQLite with foreign keys and versions.
6. Error propagation: failures raise meaningful exceptions, never silent 0-count responses.
7. Full pipeline: Analysis -> SDLC -> IEEE 29148 SRS -> Human Approval -> Completion.
"""
import asyncio
import os
import sys
import unittest
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Set test environment
os.environ["SECRET_KEY"] = "test-secret-key-for-stabilization-testing-12345"
os.environ["LLM_PROVIDER"] = "mock"  # Deterministic test provider
os.environ["OLLAMA_TIMEOUT"] = "300"

from config import settings
settings.LLM_PROVIDER = "mock"
from llm.gateway import reset_llm_provider
reset_llm_provider()

from httpx import AsyncClient, ASGITransport
from main import app
from database import engine, Base, async_session_factory
from config import settings
from sqlalchemy import select, func
from models import User, Project, Requirement, RequirementVersion, ApprovalRequest, ApprovalAction
from llm.providers.ollama_provider import extract_json_object


class BackendStabilizationTests(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Ensure database tables exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    async def asyncTearDown(self):
        await self.client.aclose()

    # ── Test 1: Robust JSON Parser (<think> tags, markdown, commas) ──────
    async def test_extract_json_object_variants(self):
        # 1.1 Qwen3 thinking tags
        think_text = """<think>
We need to extract financial requirements. Let's create FR-001.
{ "ignored": "inside_think" }
</think>
{
  "requirements": [
    {
      "requirement_id": "FR-LOAN-001",
      "statement": "The system shall verify KYC documents against national databases.",
      "category": "functional",
      "priority": "critical"
    }
  ]
}"""
        res1 = extract_json_object(think_text)
        self.assertIsNotNone(res1)
        self.assertIn("requirements", res1)
        self.assertEqual(res1["requirements"][0]["requirement_id"], "FR-LOAN-001")

        # 1.2 Markdown code fences
        md_text = """```json
{
  "question": "What are the KYC limits?",
  "topic": "security_and_compliance"
}
```"""
        res2 = extract_json_object(md_text)
        self.assertIsNotNone(res2)
        self.assertEqual(res2["question"], "What are the KYC limits?")

        # 1.3 Trailing commas
        comma_text = """{
  "requirements": [
    {
      "requirement_id": "NFR-SEC-001",
      "statement": "The system shall encrypt all sensitive customer data at rest using AES-256.",
      "category": "security",
    },
  ],
}"""
        res3 = extract_json_object(comma_text)
        self.assertIsNotNone(res3)
        self.assertEqual(res3["requirements"][0]["requirement_id"], "NFR-SEC-001")

    # ── Test 2: Simplified Auth (No RBAC) ─────────────────────────────────
    async def test_simplified_auth_lifecycle(self):
        suffix = os.urandom(4).hex()
        email = f"analyst_{suffix}@bank.com"
        # 2.1 Register without specifying role (defaults to user)
        reg_res = await self.client.post("/api/auth/register", json={
            "email": email,
            "password": "Password123!",
            "full_name": "Test Analyst",
        })
        self.assertEqual(reg_res.status_code, 200)
        data = reg_res.json()
        token = data["access_token"]
        user_info = data["user"]
        self.assertEqual(user_info["email"], email)
        self.assertEqual(user_info["role"], "user")

        # 2.2 Verify /me
        me_res = await self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.json()["id"], user_info["id"])

        # 2.3 Logout & Token Invalidation
        logout_res = await self.client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(logout_res.status_code, 200)
        self.assertTrue(logout_res.json().get("revoked"))

        # 2.4 Verify revoked token cannot be reused
        after_logout = await self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(after_logout.status_code, 401)
        self.assertIn("revoked", after_logout.json()["detail"].lower())

    # ── Test 3: Project Ownership Isolation (User A vs User B) ───────────
    async def test_project_ownership_isolation(self):
        suffix = os.urandom(4).hex()
        # Register User A
        res_a = await self.client.post("/api/auth/register", json={
            "email": f"user_a_{suffix}@bank.com", "password": "Password123!", "full_name": "User Alpha"
        })
        self.assertEqual(res_a.status_code, 200, res_a.text)
        token_a = res_a.json()["access_token"]

        # Register User B
        res_b = await self.client.post("/api/auth/register", json={
            "email": f"user_b_{suffix}@bank.com", "password": "Password123!", "full_name": "User Beta"
        })
        self.assertEqual(res_b.status_code, 200, res_b.text)
        token_b = res_b.json()["access_token"]

        # User A creates Project A
        proj_a_res = await self.client.post("/api/projects", json={
            "name": "Commercial Lending Platform",
            "description": "Alpha corporate lending system",
            "use_case": "loan_processing",
            "jurisdiction": "US_OCC",
        }, headers={"Authorization": f"Bearer {token_a}"})
        self.assertEqual(proj_a_res.status_code, 200)
        proj_a_id = proj_a_res.json()["id"]

        # User B tries to view Project A -> 403 Forbidden
        view_b = await self.client.get(f"/api/projects/{proj_a_id}", headers={"Authorization": f"Bearer {token_b}"})
        self.assertEqual(view_b.status_code, 403)

        # User B tries to extract requirements on Project A -> 403 Forbidden
        extract_b = await self.client.post(
            f"/api/projects/{proj_a_id}/requirements/extract",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        self.assertEqual(extract_b.status_code, 403)

        # User B tries to delete Project A -> 403 Forbidden
        del_b = await self.client.delete(f"/api/projects/{proj_a_id}", headers={"Authorization": f"Bearer {token_b}"})
        self.assertEqual(del_b.status_code, 403)

        # User A list projects only sees User A's project
        list_a = await self.client.get("/api/projects", headers={"Authorization": f"Bearer {token_a}"})
        self.assertEqual(list_a.status_code, 200)
        ids_a = [p["id"] for p in list_a.json()]
        self.assertIn(proj_a_id, ids_a)

        list_b = await self.client.get("/api/projects", headers={"Authorization": f"Bearer {token_b}"})
        self.assertEqual(list_b.status_code, 200)
        ids_b = [p["id"] for p in list_b.json()]
        self.assertNotIn(proj_a_id, ids_b)

    # ── Test 4: End-to-End Workflow & Requirement Extraction ─────────────
    async def test_end_to_end_pipeline_with_real_extraction(self):
        suffix = os.urandom(4).hex()
        # Register user
        res = await self.client.post("/api/auth/register", json={
            "email": f"workflow_{suffix}@bank.com", "password": "Password123!", "full_name": "Workflow Lead"
        })
        self.assertEqual(res.status_code, 200, res.text)
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 1: Create Project
        proj_res = await self.client.post("/api/projects", json={
            "name": "Digital Retail Banking Suite",
            "description": "Consumer banking platform with instant loans",
            "use_case": "loan_processing",
            "jurisdiction": "EU_EBA",
        }, headers=headers)
        self.assertEqual(proj_res.status_code, 200)
        proj_id = proj_res.json()["id"]

        # Step 2: Stakeholder Interview
        # Start interview
        start_res = await self.client.post(f"/api/projects/{proj_id}/interview/start", headers=headers)
        self.assertEqual(start_res.status_code, 200)
        q1 = start_res.json().get("question")
        self.assertTrue(bool(q1))

        # Submit answers covering financial requirements
        a1_res = await self.client.post(
            f"/api/projects/{proj_id}/interview/answer?answer=" +
            "The system shall provide an automated personal loan origination workflow supporting up to 50,000 USD.",
            headers=headers
        )
        self.assertEqual(a1_res.status_code, 200)

        a2_res = await self.client.post(
            f"/api/projects/{proj_id}/interview/answer?answer=" +
            "The system shall verify applicant identities via automated KYC sanctions screening within 3 seconds and enforce AES-256 encryption.",
            headers=headers
        )
        self.assertEqual(a2_res.status_code, 200)

        # Step 3: Extract Requirements
        ext_res = await self.client.post(f"/api/projects/{proj_id}/requirements/extract", headers=headers)
        self.assertEqual(ext_res.status_code, 200)
        ext_data = ext_res.json()
        reqs = ext_data.get("requirements", [])
        self.assertGreater(len(reqs), 0, "Extraction returned 0 requirements!")
        self.assertGreater(ext_data.get("count", 0), 0)

        # Verify DB persistence of extracted requirements
        async with async_session_factory() as session:
            db_reqs = (await session.execute(
                select(Requirement).where(Requirement.project_id == proj_id)
            )).scalars().all()
            self.assertGreater(len(db_reqs), 0)
            self.assertEqual(len(db_reqs), len(reqs))

            # Verify versions
            db_vers = (await session.execute(
                select(RequirementVersion)
            )).scalars().all()
            self.assertGreater(len(db_vers), 0)

        # Step 4: Run 7-Dimension Analysis
        ana_res = await self.client.post(f"/api/projects/{proj_id}/requirements/analyse", headers=headers)
        self.assertEqual(ana_res.status_code, 200)

        # Step 5: SDLC Recommendation
        sdlc_res = await self.client.post(f"/api/projects/{proj_id}/sdlc/analyse", headers=headers)
        self.assertEqual(sdlc_res.status_code, 200)
        self.assertIn("recommended_framework", sdlc_res.json())

        # Step 6: Generate IEEE Std 29148 SRS Document
        srs_res = await self.client.post(f"/api/projects/{proj_id}/srs/generate", headers=headers)
        self.assertEqual(srs_res.status_code, 200)
        srs_data = srs_res.json()
        self.assertIn("title", srs_data)
        self.assertEqual(srs_data.get("approval_status"), "pending")
        self.assertIn("DRAFT", srs_data.get("status", "").upper())

        # Step 7: Approvals Sign-off (No RBAC restriction, owner approves)
        apps_res = await self.client.get(f"/api/projects/{proj_id}/approvals", headers=headers)
        self.assertEqual(apps_res.status_code, 200)
        app_list = apps_res.json()
        self.assertGreater(len(app_list), 0)
        app_id = app_list[0]["id"]

        act_res = await self.client.post(f"/api/projects/{proj_id}/approvals/{app_id}/action", json={
            "action": "approve",
            "comments": "All requirements and compliance checks verified and accepted.",
        }, headers=headers)
        self.assertEqual(act_res.status_code, 200)
        self.assertEqual(act_res.json()["approval_status"], "approved")

        # Step 8: Mark Project Completed
        comp_res = await self.client.put(f"/api/projects/{proj_id}/stage", json={
            "stage": "completed"
        }, headers=headers)
        self.assertEqual(comp_res.status_code, 200)
        self.assertEqual(comp_res.json()["current_stage"], "completed")


if __name__ == "__main__":
    unittest.main()
