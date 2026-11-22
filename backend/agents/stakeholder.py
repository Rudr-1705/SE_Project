"""Stakeholder Interaction Agent — adaptive interviews and context gathering."""
import json
from agents.base import BaseAgent
from schemas.models import AgentInput, AgentOutput

INTERVIEW_TOPICS = [
   "business_and_workflow",
    "data_and_transactions",
    "security_and_compliance",
    "integrations_and_performance"
]

SYSTEM_PROMPT = """You are a concise financial requirements engineering assistant.

Conduct a stakeholder interview using exactly four main questions.

Cover these areas in order:
1. Business objectives, users, roles and workflows.
2. Data requirements, documents and transaction rules.
3. Security, privacy, KYC, AML and regulatory compliance.
4. External integrations, performance, audit and reporting.

Ask ONE short, specific question at a time.
Use previous answers to avoid repetition.
Do not ask lengthy or unnecessary follow-up questions.
Ask a follow-up only if a critical detail is missing.
Keep questions concise and easy to answer.

Return valid JSON containing:
question, topic, follow_up, reasoning.
"""

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
        for msg in conversation_history[-10:]:
            history_text += f"\n{msg.get('role', 'user')}: {msg.get('content', '')}"

        topics_remaining = [t for t in INTERVIEW_TOPICS if t not in topics_covered]

        # End interview when all topics have been covered
        if not topics_remaining:
            return AgentOutput(
                agent_name=self.name,
                status="success",
                data={
                    "question": "Thank you. We have covered all the major requirements.",
                    "topic": "wrap_up",
                    "follow_up": False,
                    "reasoning": "All interview topics have been covered.",
                    "topics_covered": topics_covered,
                    "topics_remaining": [],
                    "progress": 1.0,
                    "completed": True,
                },
                confidence=1.0,
                citations=[],
            )

        prompt = f"""Stakeholder role: {stakeholder_role}

Topics already covered: {', '.join(topics_covered) or 'None'}
Topics remaining: {', '.join(topics_remaining) or 'None'}

Conversation so far:
{history_text}

Generate exactly ONE concise question about the next uncovered topic.

Topic priority:
1. business_and_workflow
2. data_and_transactions
3. security_and_compliance
4. integrations_and_performance

Do not repeat previously covered topics.
Do not ask multiple questions in one response.
Avoid follow-ups unless a critical requirement is missing.

Return JSON with:
question, topic, follow_up, reasoning.
"""

        result = await self.llm.generate_structured(prompt, SYSTEM_PROMPT)
        response_data = result["data"]

        topic = topics_remaining[0]

        # Track the topic covered by this question
        if topic in INTERVIEW_TOPICS and topic not in topics_covered:
            topics_covered.append(topic)

        # Recalculate progress after updating topics
        updated_remaining = [
            t for t in INTERVIEW_TOPICS if t not in topics_covered
        ]

        return AgentOutput(
            agent_name=self.name,
            status="success",
            data={
                "question": response_data.get(
                    "question", "Could you elaborate on your requirements?"
                ),
                "topic": topic,
                "follow_up": response_data.get("follow_up", True),
                "reasoning": response_data.get("reasoning", ""),
                "topics_covered": topics_covered,
                "topics_remaining": updated_remaining,
                "progress": len(topics_covered) / len(INTERVIEW_TOPICS),
                "completed": not updated_remaining,
            },
            confidence=0.85,
            citations=[
                {"source": "interview_context", "model": result.get("model_info", {})}
            ],
        )
