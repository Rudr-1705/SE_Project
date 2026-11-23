"""Requirement Extraction Agent — extracts structured requirements from conversations/documents."""
import json
import logging
from agents.base import BaseAgent
from schemas.models import AgentInput, AgentOutput

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert financial software requirements engineer.
Your task is to extract clear, complete, testable requirements from stakeholder interview transcripts.

You must extract BOTH:
1. Functional Requirements (FR-LOAN-XXX): core financial business workflows, loan eligibility rules, calculations, interest calculations, user flows, application approvals.
2. Non-Functional Requirements (NFR-SEC-XXX, NFR-PERF-XXX, NFR-REG-XXX, NFR-AVAIL-XXX): security, KYC/AML regulatory compliance, audit logging, transaction performance, encryption, data privacy.

DO NOT output <think>...</think> reasoning tokens, chain-of-thought blocks, or conversational commentary.
You MUST output ONLY a valid JSON object matching the requested schema."""


class ExtractionAgent(BaseAgent):
    name = "requirement_extraction"
    responsibility = "Extract requirements from conversations/documents"
    required_permissions = []
    allowed_tools = ["llm_generate"]
    dependencies = ["stakeholder_interaction"]

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        data = agent_input.data
        source_text = data.get("text", "")
        source_type = data.get("source_type", "conversation")
        existing_ids = data.get("existing_requirement_ids", [])

        prompt = f"""Extract all functional and non-functional requirements from the following {source_type} transcript.

--- TRANSCRIPT BEGIN ---
{source_text[:12000]}
--- TRANSCRIPT END ---

Existing requirement IDs already recorded (do NOT duplicate these):
{', '.join(existing_ids) or 'None'}

Instructions:
1. Analyze every stakeholder response and question thoroughly.
2. Extract all explicit and implied requirements.
3. Every requirement must follow IEEE 29148 style ("The system shall...").
4. Classify each requirement appropriately (functional, security, performance, regulatory, data, availability, usability).
5. For each requirement, supply all fields:
   - requirement_id: unique ID (e.g. FR-LOAN-001, NFR-SEC-001, NFR-REG-001)
   - statement: clear, unambiguous, testable requirement statement ("The system shall...")
   - category: "functional", "security", "performance", "regulatory", "data", "availability", or "audit_reporting"
   - subcategory: specific area (e.g. "kyc_verification", "interest_calculation", "audit_trail", "encryption")
   - business_justification: why this requirement is essential for financial operations
   - priority: "critical", "high", "medium", or "low"
   - acceptance_criteria: list of verifiable acceptance conditions
   - applicable_regulations: list of applicable financial regulations (e.g. ["KYC", "AML", "SOX", "GDPR"])
   - risks: list of potential risks and mitigations
   - confidence: float between 0.0 and 1.0

Output strictly valid JSON with this exact format:
{{
  "requirements": [
    {{
      "requirement_id": "FR-LOAN-001",
      "statement": "The system shall...",
      "category": "functional",
      "subcategory": "loan_application",
      "priority": "high",
      "business_justification": "...",
      "acceptance_criteria": ["Criteria 1", "Criteria 2"],
      "applicable_regulations": ["KYC"],
      "risks": ["Risk description"],
      "confidence": 0.95
    }}
  ],
  "extraction_notes": "Extracted from stakeholder interview",
  "gaps_identified": []
}}
"""

        result = await self.llm.generate_structured(prompt, SYSTEM_PROMPT)
        response_data = result.get("data", {})

        # Check for model extraction error
        if isinstance(response_data, dict) and "error" in response_data:
            err_msg = response_data.get("error", "Unknown error")
            raw_sample = response_data.get("raw_output", "")[:250]
            raise RuntimeError(f"LLM requirement extraction failed: {err_msg}. Raw output: {raw_sample}")

        requirements = []
        gaps = []
        extraction_notes = "Extracted from stakeholder interview."
        confidence = 0.90

        if isinstance(response_data, list):
            requirements = response_data
        elif isinstance(response_data, dict):
            requirements = (
                response_data.get("requirements")
                or response_data.get("items")
                or response_data.get("functional_requirements")
                or []
            )
            nfrs = response_data.get("non_functional_requirements") or []
            if isinstance(nfrs, list) and nfrs:
                requirements.extend(nfrs)

            gaps = response_data.get("gaps_identified", [])
            extraction_notes = response_data.get("extraction_notes", "Extracted from stakeholder interview.")
            confidence = float(response_data.get("confidence", 0.90))

        # Normalize requirements and guarantee all required fields
        normalized = []
        for i, r in enumerate(requirements):
            if not isinstance(r, dict):
                continue
            stmt = r.get("statement", "").strip()
            if not stmt:
                continue

            cat = str(r.get("category", "functional")).lower()
            if "sec" in cat:
                prefix = "NFR-SEC"
            elif "perf" in cat:
                prefix = "NFR-PERF"
            elif "reg" in cat or "comp" in cat:
                prefix = "NFR-REG"
            elif "data" in cat:
                prefix = "NFR-DATA"
            else:
                prefix = "FR-LOAN"

            req_id = r.get("requirement_id") or f"{prefix}-{i+1:03d}"

            # Acceptance criteria normalization
            ac = r.get("acceptance_criteria", [])
            if isinstance(ac, str):
                ac = [ac]
            elif not isinstance(ac, list):
                ac = []

            # Applicable regulations normalization
            regs = r.get("applicable_regulations", [])
            if isinstance(regs, str):
                regs = [regs]
            elif not isinstance(regs, list):
                regs = []

            # Risks normalization
            risks = r.get("risks", [])
            if isinstance(risks, str):
                risks = [risks]
            elif not isinstance(risks, list):
                risks = []

            prio = str(r.get("priority", "medium")).lower()
            if prio not in ("critical", "high", "medium", "low"):
                prio = "medium"

            normalized.append({
                "requirement_id": req_id,
                "statement": stmt,
                "category": cat,
                "subcategory": r.get("subcategory", ""),
                "business_justification": r.get("business_justification", ""),
                "priority": prio,
                "acceptance_criteria": ac,
                "applicable_regulations": regs,
                "risks": risks,
                "confidence": float(r.get("confidence", 0.90)),
            })

        if not normalized and len(source_text.strip()) > 50:
            raise RuntimeError(
                "Extraction failed: The LLM returned a response, but 0 valid requirements could be parsed. "
                "Ensure local Ollama model is operating normally."
            )

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
