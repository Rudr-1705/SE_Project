"""Agent Orchestrator — central state machine coordinating all specialised agents.

Manages: agent communication, execution order, shared context, approval gates.
Pipeline: extraction → clarification → classification → conflict detection →
          compliance → security → risk → validation → documentation → SDLC → approval
"""
import logging
import json
import uuid
from datetime import datetime, timezone
from schemas.models import AgentInput, AgentOutput
from agents.stakeholder import StakeholderAgent
from agents.extraction import ExtractionAgent
from agents.clarification import ClarificationAgent
from agents.classification import ClassificationAgent
from agents.conflict import ConflictDetectionAgent
from agents.compliance import ComplianceAgent
from agents.security import SecurityAgent
from agents.risk import RiskAnalysisAgent
from agents.sdlc import SDLCAgent
from agents.documentation import DocumentationAgent
from agents.validation import ValidationAgent
from agents.approval import ApprovalAgent

logger = logging.getLogger(__name__)

# Pipeline stages in execution order
PIPELINE_STAGES = [
    "extraction", "clarification", "classification", "conflict_detection",
    "compliance", "security_privacy", "risk_analysis", "validation",
]


class Orchestrator:
    """Central state machine that coordinates all agents."""

    def __init__(self):
        self.agents = {
            "stakeholder_interaction": StakeholderAgent(),
            "requirement_extraction": ExtractionAgent(),
            "clarification": ClarificationAgent(),
            "classification": ClassificationAgent(),
            "conflict_detection": ConflictDetectionAgent(),
            "compliance": ComplianceAgent(),
            "security_privacy": SecurityAgent(),
            "risk_analysis": RiskAnalysisAgent(),
            "sdlc_selection": SDLCAgent(),
            "documentation": DocumentationAgent(),
            "validation": ValidationAgent(),
            "human_approval": ApprovalAgent(),
        }
        # Shared state per project
        self.sessions: dict[str, dict] = {}

    def _get_session(self, project_id: str) -> dict:
        if project_id not in self.sessions:
            self.sessions[project_id] = {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "stage": "idle",
                "requirements": [],
                "conversation_history": [],
                "topics_covered": [],
                "analysis_results": {},
                "approval_requests": [],
                "audit_trail": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        return self.sessions[project_id]

    async def start_interview(self, project_id: str, user_id: str,
                               stakeholder_role: str = "business_analyst") -> dict:
        """Start adaptive stakeholder interview."""
        session = self._get_session(project_id)
        session["stage"] = "interview"

        agent_input = AgentInput(
            task_id=str(uuid.uuid4()),
            agent_name="stakeholder_interaction",
            project_id=project_id,
            user_id=user_id,
            data={
                "stakeholder_role": stakeholder_role,
                "conversation_history": session["conversation_history"],
                "topics_covered": session["topics_covered"],
            },
        )

        result = await self.agents["stakeholder_interaction"].execute(agent_input)
        self._log_audit(session, "stakeholder_interaction", "interview_question", result)
        return result.data

    async def answer_interview(self, project_id: str, user_id: str, answer: str) -> dict:
        """Process stakeholder answer and generate follow-up question."""
        session = self._get_session(project_id)
        session["conversation_history"].append({"role": "user", "content": answer})

        agent_input = AgentInput(
            task_id=str(uuid.uuid4()),
            agent_name="stakeholder_interaction",
            project_id=project_id,
            user_id=user_id,
            data={
                "stakeholder_role": "business_analyst",
                "conversation_history": session["conversation_history"],
                "topics_covered": session["topics_covered"],
            },
        )

        result = await self.agents["stakeholder_interaction"].execute(agent_input)
        session["conversation_history"].append(
            {"role": "assistant", "content": result.data.get("question", "")}
        )
        if result.data.get("topic") and result.data["topic"] not in session["topics_covered"]:
            session["topics_covered"].append(result.data["topic"])

        self._log_audit(session, "stakeholder_interaction", "interview_answer", result)
        return result.data

    async def extract_requirements(self, project_id: str, user_id: str,
                                    text: str, source_type: str = "conversation") -> dict:
        """Extract structured requirements from text."""
        session = self._get_session(project_id)
        session["stage"] = "extraction"

        existing_ids = [r.get("requirement_id", "") for r in session["requirements"]]

        agent_input = AgentInput(
            task_id=str(uuid.uuid4()),
            agent_name="requirement_extraction",
            project_id=project_id,
            user_id=user_id,
            data={"text": text, "source_type": source_type, "existing_requirement_ids": existing_ids},
        )

        result = await self.agents["requirement_extraction"].execute(agent_input)
        new_reqs = result.data.get("requirements", [])
        session["requirements"].extend(new_reqs)

        self._log_audit(session, "requirement_extraction", "extract", result)
        return result.data

    async def run_analysis_pipeline(self, project_id: str, user_id: str) -> dict:
        """Run the full analysis pipeline: clarification → classification → conflict →
        compliance → security → risk → validation."""
        session = self._get_session(project_id)
        requirements = session["requirements"]
        results = {}

        if not requirements:
            return {"error": "No requirements to analyse. Extract requirements first."}

        # Stage 1: Clarification
        session["stage"] = "clarification"
        clarification = await self.agents["clarification"].execute(
            AgentInput(project_id=project_id, user_id=user_id,
                      data={"requirements": requirements})
        )
        results["clarification"] = clarification.data
        self._log_audit(session, "clarification", "analyse", clarification)

        # Stage 2: Classification
        session["stage"] = "classification"
        classification = await self.agents["classification"].execute(
            AgentInput(project_id=project_id, user_id=user_id,
                      data={"requirements": requirements})
        )
        results["classification"] = classification.data
        self._log_audit(session, "classification", "analyse", classification)

        # Stage 3: Conflict Detection
        session["stage"] = "conflict_detection"
        conflict = await self.agents["conflict_detection"].execute(
            AgentInput(project_id=project_id, user_id=user_id,
                      data={"requirements": requirements})
        )
        results["conflict_detection"] = conflict.data
        self._log_audit(session, "conflict_detection", "analyse", conflict)

        # Stage 4: Compliance
        session["stage"] = "compliance"
        compliance = await self.agents["compliance"].execute(
            AgentInput(project_id=project_id, user_id=user_id,
                      data={"requirements": requirements})
        )
        results["compliance"] = compliance.data
        self._log_audit(session, "compliance", "analyse", compliance)

        # Stage 5: Security
        session["stage"] = "security"
        security = await self.agents["security_privacy"].execute(
            AgentInput(project_id=project_id, user_id=user_id,
                      data={"requirements": requirements})
        )
        results["security"] = security.data
        self._log_audit(session, "security_privacy", "analyse", security)

        # Stage 6: Risk
        session["stage"] = "risk_analysis"
        risk = await self.agents["risk_analysis"].execute(
            AgentInput(project_id=project_id, user_id=user_id,
                      data={"requirements": requirements,
                            "compliance_analysis": compliance.data.get("compliance_analysis", []),
                            "security_analysis": security.data.get("security_analysis", [])})
        )
        results["risk_analysis"] = risk.data
        self._log_audit(session, "risk_analysis", "analyse", risk)

        # Stage 7: Validation
        session["stage"] = "validation"
        validation = await self.agents["validation"].execute(
            AgentInput(project_id=project_id, user_id=user_id,
                      data={"requirements": requirements})
        )
        results["validation"] = validation.data
        self._log_audit(session, "validation", "analyse", validation)

        session["analysis_results"] = results
        session["stage"] = "analysed"
        return results

    async def run_sdlc_analysis(self, project_id: str, user_id: str,
                                 factors: dict | None = None) -> dict:
        """Run SDLC selection analysis."""
        session = self._get_session(project_id)
        session["stage"] = "sdlc_analysis"

        agent_input = AgentInput(
            project_id=project_id, user_id=user_id,
            data={"requirements": session["requirements"], "factors": factors or {}},
        )

        result = await self.agents["sdlc_selection"].execute(agent_input)
        session["analysis_results"]["sdlc"] = result.data
        self._log_audit(session, "sdlc_selection", "analyse", result)
        return result.data

    async def generate_artefact(self, project_id: str, user_id: str,
                                 artefact_type: str, project_name: str = "") -> dict:
        """Generate a documentation artefact."""
        session = self._get_session(project_id)

        agent_input = AgentInput(
            project_id=project_id, user_id=user_id,
            data={"artefact_type": artefact_type,
                  "requirements": session["requirements"],
                  "project_name": project_name or project_id},
        )

        result = await self.agents["documentation"].execute(agent_input)
        self._log_audit(session, "documentation", "generate", result)
        return result.data

    async def request_approval(self, project_id: str, user_id: str,
                                approval_type: str, target_id: str = "",
                                description: str = "", target_data: dict = None) -> dict:
        """Create a human approval request."""
        session = self._get_session(project_id)

        agent_input = AgentInput(
            project_id=project_id, user_id=user_id,
            data={"approval_type": approval_type, "target_id": target_id,
                  "description": description, "target_data": target_data or {}},
        )

        result = await self.agents["human_approval"].execute(agent_input)
        if result.data.get("approval_request"):
            session["approval_requests"].append(result.data["approval_request"])
        self._log_audit(session, "human_approval", "request", result)
        return result.data

    def get_session_state(self, project_id: str) -> dict:
        """Get current session state for a project."""
        session = self._get_session(project_id)
        return {
            "session_id": session["id"],
            "stage": session["stage"],
            "requirement_count": len(session["requirements"]),
            "topics_covered": session["topics_covered"],
            "conversation_length": len(session["conversation_history"]),
            "has_analysis": bool(session["analysis_results"]),
            "pending_approvals": len([a for a in session["approval_requests"]
                                      if a.get("status") == "pending"]),
            "audit_count": len(session["audit_trail"]),
        }

    def get_requirements(self, project_id: str) -> list:
        """Get all extracted requirements for a project."""
        return self._get_session(project_id)["requirements"]

    def get_audit_trail(self, project_id: str) -> list:
        """Get audit trail for a project."""
        return self._get_session(project_id)["audit_trail"]

    def _log_audit(self, session: dict, agent_name: str, action: str, result: AgentOutput):
        session["audit_trail"].append({
            "agent": agent_name,
            "action": action,
            "status": result.status,
            "confidence": result.confidence,
            "issues": result.issues[:5],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "audit_entry": result.audit_entry,
        })


# Singleton orchestrator
_orchestrator: Orchestrator | None = None

def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator
