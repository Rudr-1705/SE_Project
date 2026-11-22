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

        if isinstance(response_data, list):
            requirements = response_data
            gaps = []
            extraction_notes = "Extracted from source."
            confidence = 0.88
        elif isinstance(response_data, dict):
            requirements = response_data.get("requirements") or response_data.get("items") or []
            gaps = response_data.get("gaps_identified", [])
            extraction_notes = response_data.get("extraction_notes", "")
            confidence = response_data.get("confidence", 0.88)
        else:
            requirements = []
            gaps = []
            extraction_notes = ""
            confidence = 0.5

        # Normalize requirements and guarantee required fields
        normalized = []
        for i, r in enumerate(requirements):
            if not isinstance(r, dict):
                continue
            cat = r.get("category", "functional")
            prefix = "NFR-SEC" if "sec" in cat.lower() else ("NFR-PERF" if "perf" in cat.lower() else "FR-LOAN")
            req_id = r.get("requirement_id") or f"{prefix}-{i+1:03d}"
            normalized.append({
                "requirement_id": req_id,
                "statement": r.get("statement", ""),
                "category": cat,
                "subcategory": r.get("subcategory", ""),
                "business_justification": r.get("business_justification", ""),
                "priority": r.get("priority", "medium"),
                "acceptance_criteria": r.get("acceptance_criteria") if isinstance(r.get("acceptance_criteria"), list) else [r.get("acceptance_criteria")] if r.get("acceptance_criteria") else [],
                "applicable_regulations": r.get("applicable_regulations") if isinstance(r.get("applicable_regulations"), list) else [],
                "risks": r.get("risks") if isinstance(r.get("risks"), list) else [],
                "confidence": float(r.get("confidence", 0.85)),
            })

        return AgentOutput(
            agent_name=self.name,
            status="success",
            data={
                "requirements": normalized,
                "count": len(normalized),
                "extraction_notes": extraction_notes,
                "gaps_identified": gaps,
            },
            confidence=confidence,
            citations=[{"source": source_type, "model": result.get("model_info", {})}],
            issues=[f"Gap: {g}" for g in gaps] if gaps else [],
        )

    def validate_input(self, agent_input: AgentInput) -> list[str]:
        errors = []
        if not agent_input.data.get("text"):
            errors.append("Source text is required for requirement extraction")
        return errors
