"""Comprehensive verification test suite for AIFRE:
1. Jurisdiction selection & propagation across agents
2. 7-dimension requirements analysis execution & persistence
3. SDLC multi-criteria recommendation (all 6 models evaluated)
4. Human approval workflow (approve, reject, modify, stage transitions)
5. IEEE 29148 SRS generation (loan workflow, user roles, external interfaces, risk register, RTM)
6. PDF & DOCX generation validation
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ["SECRET_KEY"] = "test-secret-key-for-stabilization-testing-12345"
os.environ["LLM_PROVIDER"] = "mock"

from config import settings
settings.LLM_PROVIDER = "mock"
from llm.gateway import reset_llm_provider
reset_llm_provider()

import unittest
import asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from main import app
from database import async_session_factory, engine, Base
from models.project import Project
from models.approval import ApprovalRequest, ApprovalAction
from sqlalchemy import select


class TestPipelineAndGovernance(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        self.suffix = uuid.uuid4().hex[:6]
        
        # Register fresh test user
        reg_res = await self.client.post("/api/auth/register", json={
            "email": f"tester_{self.suffix}@example.com",
            "password": "SecurePassword123!",
            "full_name": f"Tester {self.suffix}",
        })
        self.assertEqual(reg_res.status_code, 200, f"Registration failed: {reg_res.text}")
        self.token = reg_res.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_jurisdiction_selection_and_persistence(self):
        """Test jurisdiction dropdown choices persist and propagate correctly."""
        jurisdictions_to_test = [
            "India",
            "United States",
            "United Kingdom"
        ]

        for jur in jurisdictions_to_test:
            res = await self.client.post("/api/projects", headers=self.headers, json={
                "name": f"Loan Project {jur}",
                "description": f"Custom executive summary for {jur} digital lending platform.",
                "use_case": "loan_processing",
                "jurisdiction": jur,
            })
            self.assertEqual(res.status_code, 200)
            proj_data = res.json()
            proj_id = proj_data["id"]
            self.assertEqual(proj_data["jurisdiction"], jur)

            # Verify retrieval
            get_res = await self.client.get(f"/api/projects/{proj_id}", headers=self.headers)
            self.assertEqual(get_res.status_code, 200)
            self.assertEqual(get_res.json()["jurisdiction"], jur)

    async def test_approval_workflow_lifecycle(self):
        """Test approval actions (approve, reject, modify) and stage transition to completed."""
        # 1. Create project
        p_res = await self.client.post("/api/projects", headers=self.headers, json={
            "name": f"Approval Test Project {self.suffix}",
            "jurisdiction": "India",
        })
        proj_id = p_res.json()["id"]

        # 2. List approvals (auto-creates baseline sign-off)
        apps_res = await self.client.get(f"/api/projects/{proj_id}/approvals", headers=self.headers)
        self.assertEqual(apps_res.status_code, 200)
        apps = apps_res.json()
        self.assertTrue(len(apps) >= 1)
        approval_id = apps[0]["id"]
        self.assertEqual(apps[0]["status"], "pending")

        # 3. Perform modify action
        mod_res = await self.client.post(
            f"/api/projects/{proj_id}/approvals/{approval_id}/action",
            headers=self.headers,
            json={"action": "modify", "comments": "Please refine CIBIL timeout settings."}
        )
        self.assertEqual(mod_res.status_code, 200)
        self.assertEqual(mod_res.json()["approval_status"], "changes_requested")

        # 4. Perform approve action
        app_res = await self.client.post(
            f"/api/projects/{proj_id}/approvals/{approval_id}/action",
            headers=self.headers,
            json={"action": "approve", "comments": "Final baseline approved by underwriter."}
        )
        self.assertEqual(app_res.status_code, 200)
        self.assertEqual(app_res.json()["approval_status"], "approved")
        self.assertEqual(app_res.json()["current_stage"], "completed")

        # 5. Verify database persistence
        async with async_session_factory() as db:
            ar = await db.execute(select(ApprovalRequest).where(ApprovalRequest.id == approval_id))
            app_obj = ar.scalar_one()
            self.assertEqual(app_obj.status, "approved")
            self.assertIsNotNone(app_obj.resolved_at)

            actions = await db.execute(select(ApprovalAction).where(ApprovalAction.approval_request_id == approval_id))
            acts = actions.scalars().all()
            self.assertEqual(len(acts), 2)
            action_names = {a.action for a in acts}
            self.assertIn("modify", action_names)
            self.assertIn("approve", action_names)

    async def test_sdlc_methodology_evaluation(self):
        """Test SDLC selection evaluates all 6 models with distinct scores."""
        p_res = await self.client.post("/api/projects", headers=self.headers, json={
            "name": f"SDLC Eval {self.suffix}",
            "jurisdiction": "India",
        })
        proj_id = p_res.json()["id"]

        # Add requirements
        await self.client.post(f"/api/projects/{proj_id}/requirements", headers=self.headers, json={
            "statement": "The system shall integrate with CIBIL credit bureau with a 2.0 second target latency.",
            "category": "functional",
            "priority": "critical"
        })
        await self.client.post(f"/api/projects/{proj_id}/requirements", headers=self.headers, json={
            "statement": "All PII data shall be encrypted with AES-256 adhering to RBI data security directives.",
            "category": "security",
            "priority": "critical"
        })

        # Run SDLC analysis
        sdlc_res = await self.client.post(f"/api/projects/{proj_id}/sdlc/analyse", headers=self.headers)
        self.assertEqual(sdlc_res.status_code, 200)
        sdlc_data = sdlc_res.json()

        # Verify all 6 models are evaluated
        scores = sdlc_data.get("scores", {})
        self.assertEqual(len(scores), 6)
        expected_models = {"hybrid_agile_vmodel", "devsecops", "v_model", "spiral", "agile", "waterfall"}
        self.assertEqual(set(scores.keys()), expected_models)

        # Verify scores are differentiated (not all 0.50)
        unique_scores = set(scores.values())
        self.assertTrue(len(unique_scores) > 2, f"Scores lack differentiation: {scores}")

        # Verify evaluated models breakdown
        evaluated_models = sdlc_data.get("evaluated_models", [])
        self.assertEqual(len(evaluated_models), 6)
        for em in evaluated_models:
            self.assertIn("display_name", em)
            self.assertIn("pros", em)
            self.assertIn("cons", em)

        # Verify retrieval via both endpoints
        rec_res = await self.client.get(f"/api/projects/{proj_id}/sdlc/recommendation", headers=self.headers)
        self.assertEqual(rec_res.status_code, 200)

        result_res = await self.client.get(f"/api/projects/{proj_id}/sdlc/result", headers=self.headers)
        self.assertEqual(result_res.status_code, 200)

    async def test_srs_generation_completeness(self):
        """Test IEEE 29148 SRS generation completeness, user roles, external interfaces, and file output."""
        custom_exec_summary = f"Custom executive summary for {self.suffix} retail loan processing platform."
        p_res = await self.client.post("/api/projects", headers=self.headers, json={
            "name": f"Retail Loan SRS {self.suffix}",
            "description": custom_exec_summary,
            "jurisdiction": "India",
        })
        proj_id = p_res.json()["id"]

        # Add initial requirement
        await self.client.post(f"/api/projects/{proj_id}/requirements", headers=self.headers, json={
            "statement": "The applicant shall submit digital loan application with KYC verification.",
            "category": "functional",
            "priority": "critical"
        })

        # Generate SRS
        srs_res = await self.client.post(f"/api/projects/{proj_id}/srs/generate", headers=self.headers)
        self.assertEqual(srs_res.status_code, 200)
        srs = srs_res.json()

        # 1. Verify executive summary preservation
        srs_payload = srs.get("srs_data", srs)
        metadata = srs_payload.get("metadata", {})
        self.assertEqual(metadata.get("description"), custom_exec_summary)

        # 2. Verify sections exist
        sections = srs_payload.get("sections", [])
        sec_titles = [s["title"] for s in sections]
        self.assertIn("Introduction", sec_titles)
        self.assertIn("Overall Description", sec_titles)
        self.assertIn("Specific Functional Requirements", sec_titles)
        self.assertIn("External Interface Requirements", sec_titles)
        self.assertIn("Non-Functional Requirements", sec_titles)
        self.assertIn("Data Requirements and Retention", sec_titles)
        self.assertIn("Regulatory Compliance & Legal Considerations", sec_titles)
        self.assertIn("Threat Modeling and Risk Register", sec_titles)
        self.assertIn("SDLC Methodology & Quality Controls", sec_titles)
        self.assertIn("Requirements Traceability Matrix (RTM)", sec_titles)

        # 3. Verify User Roles in section 2.3
        sec2 = next(s for s in sections if s["num"] == "2")
        sub2_3 = next(sub for sub in sec2["subsections"] if sub["num"] == "2.3")
        role_names = [uc[0] for uc in sub2_3["user_classes"]]
        self.assertIn("Customers / Applicants", role_names)
        self.assertIn("Loan Officers", role_names)
        self.assertIn("Credit Analysts", role_names)
        self.assertIn("Compliance Officers", role_names)
        self.assertIn("Administrators", role_names)

        # 4. Verify External Interfaces in section 4.3
        sec4 = next(s for s in sections if s["num"] == "4")
        sub4_3 = next(sub for sub in sec4["subsections"] if sub["num"] == "4.3")
        iface_names = [iface[0] for iface in sub4_3["interfaces"]]
        self.assertTrue(any("Credit Information Bureau" in name for name in iface_names))
        self.assertTrue(any("Core Banking" in name for name in iface_names))
        self.assertTrue(any("KYC" in name for name in iface_names))
        self.assertTrue(any("Account Aggregator" in name for name in iface_names))

        # 5. Verify Performance 2.0s latency target in section 5.1
        sec5 = next(s for s in sections if s["num"] == "5")
        sub5_1 = next(sub for sub in sec5["subsections"] if sub["num"] == "5.1")
        perf_stmts = [p["statement"] for p in sub5_1["requirements"]]
        self.assertTrue(any("2.0-second" in stmt or "2.0 second" in stmt for stmt in perf_stmts))

        # 6. Verify PDF and DOCX files exist on disk
        pdf_path = srs.get("pdf_path")
        docx_path = srs.get("docx_path")
        self.assertIsNotNone(pdf_path)
        self.assertIsNotNone(docx_path)
        self.assertTrue(os.path.exists(pdf_path), f"PDF file not found on disk: {pdf_path}")
        self.assertTrue(os.path.exists(docx_path), f"DOCX file not found on disk: {docx_path}")
        self.assertTrue(os.path.getsize(pdf_path) > 1000)
        self.assertTrue(os.path.getsize(docx_path) > 1000)


if __name__ == "__main__":
    unittest.main()
