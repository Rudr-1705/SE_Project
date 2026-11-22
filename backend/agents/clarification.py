"""Clarification Agent — detects ambiguous/incomplete info and generates follow-up questions."""
import json
from agents.base import BaseAgent
from schemas.models import AgentInput, AgentOutput

SYSTEM_PROMPT = """You are a requirements clarification specialist for financial systems.
Analyse requirements for ambiguity, incompleteness, vagueness, and missing details.
Generate targeted follow-up questions (NOT generic questionnaires).
Respond with JSON: clarification_needed (bool), questions (array of {target_requirement, question, reason, priority})."""


class ClarificationAgent(BaseAgent):
    name = "clarification"
    responsibility = "Detect and resolve missing/ambiguous information through follow-up questions"
    required_permissions = ["agents.execute"]
    allowed_tools = ["llm_generate"]
    dependencies = ["requirement_extraction"]

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        requirements = agent_input.data.get("requirements", [])
        if not requirements:
            return AgentOutput(agent_name=self.name, status="success",
                             data={"clarification_needed": False, "questions": []}, confidence=1.0)

        req_text = json.dumps(requirements[:20], indent=2)
        prompt = f"""Analyse these financial requirements for ambiguity, incompleteness, and vagueness.
Generate specific follow-up questions for unclear items.

Requirements:
{req_text}

For each issue found provide:
- target_requirement: the requirement ID
- question: specific clarification question
- reason: why clarification is needed
- priority: high/medium/low
Respond as JSON."""

        result = await self.llm.generate_structured(prompt, SYSTEM_PROMPT)
        response_data = result["data"]

        if isinstance(response_data, list):
            questions = response_data
        elif isinstance(response_data, dict):
            questions = response_data.get("questions") or response_data.get("items") or []
        else:
            questions = []

        if not questions and requirements:
            # If the model didn't flag any, generate targeted verification questions for the first requirements
            for r in requirements[:2]:
                questions.append({
                    "target_requirement": r.get("requirement_id", "REQ-001"),
                    "question": f"For {r.get('requirement_id')}: What are the specific threshold values and external service timeout limits?",
                    "reason": "Specification of exact boundary conditions and SLA latency constraints.",
                    "priority": "medium"
                })

        return AgentOutput(
            agent_name=self.name, status="success",
            data={
                "clarification_needed": len(questions) > 0,
                "questions": questions,
                "count": len(questions),
                "total_analysed": len(requirements),
            },
            confidence=response_data.get("confidence", 0.85) if isinstance(response_data, dict) else 0.85,
            issues=[f"Clarification needed: {q.get('target_requirement','')}" for q in questions],
        )
