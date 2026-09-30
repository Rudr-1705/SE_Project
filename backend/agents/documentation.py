"""Documentation Agent — generates SRS, user stories, use cases, and traceability records."""
import json
from agents.base import BaseAgent
from schemas.models import AgentInput, AgentOutput

SYSTEM_PROMPT = """You are a requirements documentation specialist for financial systems.
Generate professional artefacts maintaining traceability to source requirements and evidence.
Every generated item MUST retain links to its original requirement ID and supporting evidence."""


class DocumentationAgent(BaseAgent):
    name = "documentation"
    responsibility = "Generate SRS, user stories, use cases and traceability records"
    required_permissions = ["agents.execute"]
    allowed_tools = ["llm_generate"]
    dependencies = ["validation"]

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        artefact_type = agent_input.data.get("artefact_type", "srs")
        requirements = agent_input.data.get("requirements", [])
        project_name = agent_input.data.get("project_name", "Financial System")

        generators = {
            "srs": self._generate_srs,
            "user_stories": self._generate_user_stories,
            "use_cases": self._generate_use_cases,
            "acceptance_criteria": self._generate_acceptance_criteria,
            "rtm": self._generate_rtm,
            "compliance_matrix": self._generate_compliance_matrix,
            "threat_risk_register": self._generate_risk_register,
            "sdlc_workflow": self._generate_sdlc_workflow,
        }

        generator = generators.get(artefact_type, self._generate_srs)
        result = await generator(requirements, project_name)

        return AgentOutput(
            agent_name=self.name, status="success",
            data={"artefact_type": artefact_type, "content": result["content"],
                  "title": result["title"], "source_requirements": result.get("sources", [])},
            confidence=0.88,
        )

    async def _generate_srs(self, requirements: list, project_name: str) -> dict:
        req_text = json.dumps(requirements[:30], indent=2)
        prompt = f"""Generate a Software Requirements Specification (SRS) for "{project_name}".

Requirements:
{req_text}

Include: Introduction, Scope, Functional Requirements, Non-Functional Requirements,
Security Requirements, Compliance Requirements, Constraints, Assumptions.
Each section must reference source requirement IDs.
Output as structured JSON with sections."""

        result = await self.llm.generate(prompt, SYSTEM_PROMPT)
        return {"title": f"SRS — {project_name}", "content": result["content"],
                "sources": [r.get("requirement_id", "") for r in requirements]}

    async def _generate_user_stories(self, requirements: list, project_name: str) -> dict:
        req_text = json.dumps(requirements[:20], indent=2)
        prompt = f"""Generate user stories with acceptance criteria for "{project_name}".
Format: As a [role], I want [feature] so that [benefit].
Each must link to source requirement ID.
Requirements:
{req_text}
Respond as JSON with user_stories array."""

        result = await self.llm.generate(prompt, SYSTEM_PROMPT)
        return {"title": f"User Stories — {project_name}", "content": result["content"],
                "sources": [r.get("requirement_id", "") for r in requirements]}

    async def _generate_use_cases(self, requirements: list, project_name: str) -> dict:
        req_text = json.dumps(requirements[:15], indent=2)
        prompt = f"""Generate use cases for "{project_name}".
Each use case: ID, title, actor, preconditions, main flow, alternative flows, postconditions, source requirements.
Requirements:
{req_text}
Respond as JSON."""

        result = await self.llm.generate(prompt, SYSTEM_PROMPT)
        return {"title": f"Use Cases — {project_name}", "content": result["content"],
                "sources": [r.get("requirement_id", "") for r in requirements]}

    async def _generate_acceptance_criteria(self, requirements: list, project_name: str) -> dict:
        req_text = json.dumps(requirements[:20], indent=2)
        prompt = f"""Generate detailed acceptance criteria for each requirement in "{project_name}".
Requirements: {req_text}
Respond as JSON."""
        result = await self.llm.generate(prompt, SYSTEM_PROMPT)
        return {"title": f"Acceptance Criteria — {project_name}", "content": result["content"],
                "sources": [r.get("requirement_id", "") for r in requirements]}

    async def _generate_rtm(self, requirements: list, project_name: str) -> dict:
        entries = []
        for r in requirements:
            entries.append({
                "requirement_id": r.get("requirement_id", ""),
                "statement": r.get("statement", "")[:100],
                "source": r.get("source", ""),
                "category": r.get("category", ""),
                "regulations": r.get("applicable_regulations", []),
                "risks": [risk.get("description", "")[:50] for risk in r.get("risks", [])],
                "acceptance_criteria": r.get("acceptance_criteria", []),
                "status": r.get("status", "extracted"),
            })
        content = json.dumps({"traceability_matrix": entries}, indent=2)
        return {"title": f"Requirements Traceability Matrix — {project_name}", "content": content,
                "sources": [r.get("requirement_id", "") for r in requirements]}

    async def _generate_compliance_matrix(self, requirements: list, project_name: str) -> dict:
        entries = []
        for r in requirements:
            if r.get("applicable_regulations"):
                entries.append({
                    "requirement_id": r.get("requirement_id", ""),
                    "regulations": r.get("applicable_regulations", []),
                    "controls": r.get("applicable_controls", []),
                    "status": "mapped",
                })
        content = json.dumps({"compliance_matrix": entries}, indent=2)
        return {"title": f"Compliance Control Matrix — {project_name}", "content": content,
                "sources": [e["requirement_id"] for e in entries]}

    async def _generate_risk_register(self, requirements: list, project_name: str) -> dict:
        risks = []
        for r in requirements:
            for risk in r.get("risks", []):
                risks.append({**risk, "source_requirement": r.get("requirement_id", "")})
        content = json.dumps({"threat_risk_register": risks}, indent=2)
        return {"title": f"Threat/Risk Register — {project_name}", "content": content,
                "sources": [r.get("requirement_id", "") for r in requirements if r.get("risks")]}

    async def _generate_sdlc_workflow(self, requirements: list, project_name: str) -> dict:
        prompt = f"""Generate a project-specific SDLC workflow for the financial system "{project_name}".
Include: phases, activities, responsible roles, deliverables, security activities,
testing, compliance checkpoints, approval gates, entry/exit criteria.
Include financial controls: threat modelling (design), static security testing (implementation),
transaction-integrity testing (validation), compliance approval (deployment).
Respond as JSON."""
        result = await self.llm.generate(prompt, SYSTEM_PROMPT)
        return {"title": f"SDLC Workflow — {project_name}", "content": result["content"],
                "sources": []}
