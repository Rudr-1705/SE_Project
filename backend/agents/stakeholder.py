"""Stakeholder Interaction Agent — adaptive interviews and context gathering."""
import json
from agents.base import BaseAgent
from schemas.models import AgentInput, AgentOutput

INTERVIEW_TOPICS = [
    "business_objectives", "users_roles", "workflow",
    "data_requirements", "security", "compliance",
    "integration", "performance", "exceptional_conditions",
    "audit_reporting", "transaction_limits", "schedule_budget"
]

SYSTEM_PROMPT = """You are a financial requirements engineering assistant conducting a stakeholder interview.
Your role is to gather comprehensive requirements for a financial system.
Ask targeted, specific questions based on the stakeholder's role and previous answers.
Do NOT ask generic questions. Adapt based on what has been discussed.
Respond with JSON containing: question, topic, follow_up (bool), reasoning.
Topics to cover: business objectives, users/roles, workflows, data requirements,
security, compliance, integrations, performance, exceptions, audit/reporting."""


class StakeholderAgent(BaseAgent):
    name = "stakeholder_interaction"
    responsibility = "Conduct adaptive interviews and gather missing context"
    required_permissions = ["agents.execute"]
    allowed_tools = ["llm_generate"]
    dependencies = []

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        data = agent_input.data
        stakeholder_role = data.get("stakeholder_role", "business_analyst")
        conversation_history = data.get("conversation_history", [])
        topics_covered = data.get("topics_covered", [])

        # Build context from conversation history
        history_text = ""
        for msg in conversation_history[-10:]:  # Last 10 messages
            history_text += f"\n{msg.get('role', 'user')}: {msg.get('content', '')}"

        topics_remaining = [t for t in INTERVIEW_TOPICS if t not in topics_covered]
        progress = len(topics_covered) / len(INTERVIEW_TOPICS)

        prompt = f"""Stakeholder role: {stakeholder_role}
Topics already covered: {', '.join(topics_covered) or 'None'}
Topics remaining: {', '.join(topics_remaining) or 'None'}
Conversation so far:{history_text}

Generate the next interview question. Focus on topics not yet covered.
If the previous answer was vague or incomplete, ask a follow-up to clarify.
Respond as JSON with: question, topic, follow_up, reasoning."""

        result = await self.llm.generate_structured(prompt, SYSTEM_PROMPT)
        response_data = result["data"]

        # Track which topic this question covers
        topic = response_data.get("topic", "general")
        if topic not in topics_covered and topic in INTERVIEW_TOPICS:
            topics_covered.append(topic)

        return AgentOutput(
            agent_name=self.name,
            status="success",
            data={
                "question": response_data.get("question", "Could you elaborate on your requirements?"),
                "topic": topic,
                "follow_up": response_data.get("follow_up", True),
                "reasoning": response_data.get("reasoning", ""),
                "topics_covered": topics_covered,
                "topics_remaining": topics_remaining,
                "progress": progress,
            },
            confidence=0.85,
            citations=[{"source": "interview_context", "model": result.get("model_info", {})}],
        )
