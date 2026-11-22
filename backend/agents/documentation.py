"""Documentation Agent — generates IEEE 29148 compliant SRS Document (PDF, DOCX, and JSON)."""
import os
import uuid
from pathlib import Path
from agents.base import BaseAgent
from schemas.models import AgentInput, AgentOutput
from agents.srs_generator import build_ieee_srs_data, generate_srs_pdf, generate_srs_docx
from config import settings


class DocumentationAgent(BaseAgent):
    name = "documentation"
    responsibility = "Generate comprehensive IEEE 29148 compliant Software Requirements Specification (SRS)"
    required_permissions = ["agents.execute"]
    allowed_tools = ["llm_generate"]
    dependencies = ["validation"]

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        data = agent_input.data
        project_id = agent_input.project_id or "default"
        project_name = data.get("project_name", "Financial System")
        project_desc = data.get("project_description", "")
        requirements = data.get("requirements", [])
        compliance_data = data.get("compliance_analysis", [])
        security_data = data.get("security_analysis", [])
        risk_data = data.get("risk_assessment", [])
        sdlc_data = data.get("sdlc", {})
        jurisdiction = data.get("jurisdiction", "US")
        approval_status = data.get("approval_status", "pending")

        # Build IEEE 29148 SRS Data Structure
        srs_data = build_ieee_srs_data(
            project_name=project_name,
            project_desc=project_desc,
            requirements=requirements,
            compliance_data=compliance_data,
            security_data=security_data,
            risk_data=risk_data,
            sdlc_data=sdlc_data,
            jurisdiction=jurisdiction,
            approval_status=approval_status,
        )

        # File output paths
        docs_dir = settings.DATA_DIR / "srs" / project_id
        docs_dir.mkdir(parents=True, exist_ok=True)

        safe_name = "".join(c for c in project_name if c.isalnum() or c in ("-", "_")).rstrip() or "Financial_System"
        pdf_path = str(docs_dir / f"SRS_{safe_name}.pdf")
        docx_path = str(docs_dir / f"SRS_{safe_name}.docx")

        # Generate files
        generate_srs_pdf(srs_data, pdf_path)
        generate_srs_docx(srs_data, docx_path)

        return AgentOutput(
            agent_name=self.name,
            status="success",
            data={
                "artefact_type": "srs",
                "title": srs_data["metadata"]["title"],
                "system_name": project_name,
                "version": srs_data["metadata"]["version"],
                "srs_data": srs_data,
                "pdf_path": pdf_path,
                "docx_path": docx_path,
                "pdf_filename": f"SRS_{safe_name}.pdf",
                "docx_filename": f"SRS_{safe_name}.docx",
                "functional_count": len([r for r in requirements if r.get("category") == "functional"]),
                "non_functional_count": len([r for r in requirements if r.get("category") != "functional"]),
                "total_requirements": len(requirements),
                "source_requirements": [r.get("requirement_id", "") for r in requirements],
            },
            confidence=0.95,
        )
