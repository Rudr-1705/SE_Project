"""Requirement Extraction Agent — extracts structured requirements from conversations/documents."""
import json
from agents.base import BaseAgent
from schemas.models import AgentInput, AgentOutput

SYSTEM_PROMPT = """You are a financial requirements extraction specialist.
Extract structured requirements from stakeholder conversations and documents.
Each requirement must have: requirement_id, statement, category, subcategory,
business_justification, priority, acceptance_criteria, applicable_regulations,
risks, and confidence score.
Use IDs like FR-LOAN-XXX for functional, NFR-SEC-XXX for security, etc.
Respond with JSON containing: requirements (array), extraction_notes, confidence, gaps_identified."""


class ExtractionAgent(BaseAgent):
    name = "requirement_extraction"
    responsibility = "Extract requirements from conversations/documents"
    required_permissions = ["agents.execute"]
    allowed_tools = ["llm_generate"]
    dependencies = ["stakeholder_interaction"]

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        data = agent_input.data
        source_text = data.get("text", "")
        source_type = data.get("source_type", "conversation")
        existing_ids = data.get("existing_requirement_ids", [])

        prompt = f"""Extract structured requirements from the following {source_type}.
Existing requirement IDs (avoid duplicates): {', '.join(existing_ids) or 'None'}

Source text:
{source_text[:8000]}

Extract ALL identifiable requirements. For each provide:
- requirement_id (unique, following pattern FR-LOAN-XXX or NFR-XXX-XXX)
- statement (clear, unambiguous, testable)
- category, subcategory
- business_justification
- priority (critical/high/medium/low)
- acceptance_criteria (list)
- applicable_regulations (list)
- risks (list with description, level, mitigation)
- confidence (0.0-1.0)

Also identify any gaps in the input.
Respond as JSON with: requirements, extraction_notes, confidence, gaps_identified."""

        result = await self.llm.generate_structured(prompt, SYSTEM_PROMPT)
        response_data = result["data"]

        requirements = response_data.get("requirements", [])
        gaps = response_data.get("gaps_identified", [])

        return AgentOutput(
            agent_name=self.name,
            status="success",
            data={
                "requirements": requirements,
                "count": len(requirements),
                "extraction_notes": response_data.get("extraction_notes", ""),
                "gaps_identified": gaps,
            },
            confidence=response_data.get("confidence", 0.8),
            citations=[{"source": source_type, "model": result.get("model_info", {})}],
            issues=[f"Gap: {g}" for g in gaps] if gaps else [],
        )

    def validate_input(self, agent_input: AgentInput) -> list[str]:
        errors = []
        if not agent_input.data.get("text"):
            errors.append("Source text is required for requirement extraction")
        return errors
