"""Compliance Agent — maps requirements to regulations and identifies compliance gaps.
IMPORTANT: This agent does NOT make final legal determinations.
High-impact interpretations are routed to human compliance/legal reviewers."""
import json
from agents.base import BaseAgent
from schemas.models import AgentInput, AgentOutput

SYSTEM_PROMPT = """You are an advisory compliance analysis assistant for financial systems.
For each requirement, identify applicable regulations, required controls, compliance gaps,
and data retention obligations. You MUST NOT make final legal determinations.
Flag high-impact interpretations for human compliance/legal review.
All output is ADVISORY ONLY.
Respond with JSON: compliance_analysis (array), disclaimer (string), confidence."""

DISCLAIMER = ("This analysis is advisory only. Final compliance determinations "
               "must be made by qualified legal and compliance personnel.")


class ComplianceAgent(BaseAgent):
    name = "compliance"
    responsibility = "Map requirements to regulations/policies and identify compliance gaps"
    required_permissions = ["agents.execute"]
    allowed_tools = ["llm_generate", "rag_retrieve"]
    dependencies = ["classification"]

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        requirements = agent_input.data.get("requirements", [])
        evidence = agent_input.data.get("evidence", [])

        req_text = json.dumps(requirements[:15], indent=2)
        evidence_text = json.dumps(evidence[:10], indent=2) if evidence else "No evidence provided"

        prompt = f"""Analyse these financial requirements for compliance. For each requirement determine:
- applicable_regulations (with jurisdiction and relevance)
- required_controls
- compliance_gaps
- evidence from knowledge base
- whether approval is required
- data_retention obligations

Requirements:
{req_text}

Available evidence/knowledge:
{evidence_text}

IMPORTANT: All output is advisory. Do NOT make final legal determinations.
Flag high-impact interpretations for human review.
Respond as JSON."""

        result = await self.llm.generate_structured(prompt, SYSTEM_PROMPT)
        response_data = result["data"]
        analysis = response_data.get("compliance_analysis", [])

        # Identify items needing human review
        items_needing_review = [a for a in analysis if a.get("approval_required")]

        return AgentOutput(
            agent_name=self.name, status="success",
            data={"compliance_analysis": analysis, "disclaimer": DISCLAIMER,
                  "items_needing_review": len(items_needing_review),
                  "total_analysed": len(analysis)},
            confidence=response_data.get("confidence", 0.78),
            issues=[f"Compliance gap: {a.get('compliance_gaps', [])}" for a in analysis
                    if a.get("compliance_gaps")],
            citations=[{"source": "compliance_analysis", "model": result.get("model_info", {})}],
        )

    def should_escalate(self, output: AgentOutput) -> bool:
        if output.data.get("items_needing_review", 0) > 0:
            return True
        return super().should_escalate(output)
