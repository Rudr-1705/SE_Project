"""Human Approval Agent — routes critical decisions to authorised personnel."""
from agents.base import BaseAgent
from schemas.models import AgentInput, AgentOutput

# Decisions requiring human approval and their required reviewer roles
APPROVAL_REQUIREMENTS = {
    "requirement_baseline": ["project_manager", "business_analyst"],
    "regulatory_interpretation": ["compliance_officer"],
    "high_risk_security": ["security_officer"],
    "stakeholder_conflict": ["project_manager"],
    "architecture_critical": ["architect"],
    "sdlc_selection": ["project_manager", "architect", "security_officer", "compliance_officer"],
    "requirement_change": ["project_manager"],
    "production_readiness": ["project_manager", "architect", "security_officer", "compliance_officer"],
}


class ApprovalAgent(BaseAgent):
    name = "human_approval"
    responsibility = "Route critical decisions to authorised personnel"
    required_permissions = ["agents.execute"]
    allowed_tools = []
    dependencies = []

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        approval_type = agent_input.data.get("approval_type", "")
        target_id = agent_input.data.get("target_id", "")
        target_data = agent_input.data.get("target_data", {})
        description = agent_input.data.get("description", "")

        required_roles = APPROVAL_REQUIREMENTS.get(approval_type, ["project_manager"])

        approval_request = {
            "approval_type": approval_type,
            "title": f"Approval Required: {approval_type.replace('_', ' ').title()}",
            "description": description,
            "target_id": target_id,
            "target_data": target_data,
            "required_roles": required_roles,
            "status": "pending",
        }

        return AgentOutput(
            agent_name=self.name, status="needs_human_review",
            data={"approval_request": approval_request, "required_roles": required_roles},
            confidence=1.0,
            next_actions=["await_human_approval"],
        )
