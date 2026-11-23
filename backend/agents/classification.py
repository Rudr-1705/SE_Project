"""Classification Agent — categorises requirements across business/domain dimensions."""
import json
from agents.base import BaseAgent
from schemas.models import AgentInput, AgentOutput

SYSTEM_PROMPT = """You are a requirements classification specialist for financial systems.
Classify each requirement into primary category and subcategories. Support multi-label classification.
Categories: functional, non_functional, security, privacy, regulatory, performance,
availability, usability, data, integration, audit_reporting, operational.
Respond with JSON: classifications (array of {requirement_id, primary_category, subcategories, labels})."""


class ClassificationAgent(BaseAgent):
    name = "classification"
    responsibility = "Classify functional/non-functional and domain categories"
    required_permissions = ["agents.execute"]
    allowed_tools = ["llm_generate"]
    dependencies = ["requirement_extraction"]

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        requirements = agent_input.data.get("requirements", [])
        if not requirements:
            return AgentOutput(agent_name=self.name, status="success",
                             data={"classifications": []}, confidence=1.0)

        compact_reqs = "\n".join([f"- {r.get('requirement_id', f'REQ-{i+1}')}: {r.get('statement', '').strip()}" for i, r in enumerate(requirements[:15])])
        prompt = f"""Classify these financial requirements. For each provide primary category,
subcategories, and domain labels. Use multi-label where appropriate.

Requirements:
{compact_reqs}

Respond as JSON with classifications array."""

        result = await self.llm.generate_structured(prompt, SYSTEM_PROMPT, max_tokens=600)
        response_data = result["data"]
        classifications = response_data.get("classifications", [])

        return AgentOutput(
            agent_name=self.name, status="success",
            data={"classifications": classifications, "count": len(classifications),
                  "rationale": response_data.get("multi_label_rationale", "")},
            confidence=response_data.get("confidence", 0.88),
        )
