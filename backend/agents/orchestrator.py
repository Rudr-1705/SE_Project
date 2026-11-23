"""Agent Orchestrator — central state machine coordinating all specialised agents.

Manages: agent communication, execution order, shared context, approval gates, DB persistence.
Pipeline: interview → extraction → clarification → classification → conflict detection →
          compliance → security → risk → validation → SDLC → SRS documentation → human approval
"""
import logging
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
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

# Sequential Pipeline stages in execution order
PIPELINE_STAGES = [
    "interview", "extraction", "analysis", "sdlc", "srs", "approval", "completed"
]


class Orchestrator:
    """Central state machine that coordinates all agents with persistent state."""

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
        # In-memory session cache per project
        self.sessions: dict[str, dict] = {}

    def _get_session(self, project_id: str) -> dict:
        if project_id not in self.sessions:
            self.sessions[project_id] = {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "stage": "interview",
                "requirements": [],
                "conversation_history": [],
                "topics_covered": [],
                "analysis_results": {},
                "srs_result": None,
                "approval_requests": [],
                "audit_trail": [],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        return self.sessions[project_id]

    async def sync_from_db(self, project_id: str, db=None) -> dict:
        """Hydrate in-memory session with database records to survive restarts."""
        session = self._get_session(project_id)
        if db is None:
            return session

        try:
            from sqlalchemy import select
            from models.project import Project
            from models.requirement import Requirement
            from models.approval import ApprovalRequest

            # 1. Project metadata & stage
            res = await db.execute(select(Project).where(Project.id == project_id))
            proj = res.scalar_one_or_none()
            if proj:
                if proj.current_stage:
                    session["stage"] = proj.current_stage
                meta = proj.metadata_ or {}
                if meta.get("conversation_history"):
                    if len(meta["conversation_history"]) >= len(session.get("conversation_history", [])):
                        session["conversation_history"] = meta["conversation_history"]
                if meta.get("topics_covered"):
                    session["topics_covered"] = meta["topics_covered"]
                if meta.get("analysis_results"):
                    session["analysis_results"] = meta["analysis_results"]
                if meta.get("srs_result"):
                    session["srs_result"] = meta["srs_result"]

            # 2. Database requirements
            req_res = await db.execute(
                select(Requirement)
                .where(Requirement.project_id == project_id, Requirement.is_current == True)
                .order_by(Requirement.requirement_id.asc())
            )
            db_reqs = req_res.scalars().all()
            if db_reqs:
                # Merge with DB
                loaded = []
                for r in db_reqs:
                    loaded.append({
                        "id": r.id,
                        "requirement_id": r.requirement_id,
                        "statement": r.statement,
                        "category": r.category,
                        "subcategory": r.subcategory or "",
                        "priority": r.priority,
                        "business_justification": r.business_justification or "",
                        "acceptance_criteria": r.acceptance_criteria or [],
                        "applicable_regulations": r.applicable_regulations or [],
                        "risks": r.risks or [],
                        "confidence": float(r.confidence or 0.85),
                        "status": r.status,
                        "source": r.source or "",
                    })
                session["requirements"] = loaded

            # 3. Approvals
            app_res = await db.execute(
                select(ApprovalRequest).where(ApprovalRequest.project_id == project_id)
            )
            db_approvals = app_res.scalars().all()
            if db_approvals:
                session["approval_requests"] = [
                    {
                        "id": a.id,
                        "title": a.title,
                        "status": a.status,
                        "request_type": a.request_type,
                        "required_roles": a.required_roles,
                    }
                    for a in db_approvals
                ]

        except Exception as e:
            logger.error(f"Error synchronizing session from DB: {e}")

        return session

    async def persist_to_db(self, project_id: str, db=None, stage: str = None):
        """Persist session state into Project database record and write agent audit logs."""
        session = self._get_session(project_id)
        if stage:
            session["stage"] = stage
        if db is None:
            return

        try:
            from sqlalchemy import select
            from models.project import Project
            from models.audit import AuditLog

            res = await db.execute(select(Project).where(Project.id == project_id))
            proj = res.scalar_one_or_none()
            if proj:
                if stage:
                    proj.current_stage = stage
                meta = dict(proj.metadata_ or {})
                meta["conversation_history"] = session.get("conversation_history", [])
                meta["topics_covered"] = session.get("topics_covered", [])
                meta["analysis_results"] = session.get("analysis_results", {})
                if session.get("srs_result"):
                    meta["srs_result"] = session["srs_result"]
                proj.metadata_ = meta

                # Persist uncommitted agent audit logs to the persistent database
                for entry in session.get("audit_trail", []):
                    if not entry.get("_db_persisted"):
                        db.add(AuditLog(
                            event_type="agent",
                            action=entry.get("action", "execute"),
                            project_id=project_id,
                            agent_name=entry.get("agent", ""),
                            description=f"Agent '{entry.get('agent')}' executed '{entry.get('action')}' ({entry.get('status')})",
                            details={
                                "status": entry.get("status"),
                                "confidence": entry.get("confidence"),
                                "issues": entry.get("issues", []),
                            }
                        ))
                        entry["_db_persisted"] = True

                await db.flush()
        except Exception as e:
            logger.error(f"Error persisting session to DB: {e}")

    async def start_interview(self, project_id: str, user_id: str,
                               stakeholder_role: str = "business_analyst", db=None) -> dict:
        """Start adaptive stakeholder interview."""
        await self.sync_from_db(project_id, db)
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
        question = result.data.get("question", "")
        # Add initial assistant greeting if history is empty
        if not session["conversation_history"]:
            session["conversation_history"].append({"role": "assistant", "content": question})

        self._log_audit(session, "stakeholder_interaction", "interview_start", result)
        await self.persist_to_db(project_id, db, stage="interview")
        return result.data

    async def answer_interview(self, project_id: str, user_id: str, answer: str, db=None) -> dict:
        """Process stakeholder answer and generate follow-up question."""
        await self.sync_from_db(project_id, db)
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
        next_q = result.data.get("question", "")
        session["conversation_history"].append({"role": "assistant", "content": next_q})

        if result.data.get("topic") and result.data["topic"] not in session["topics_covered"]:
            session["topics_covered"].append(result.data["topic"])

        self._log_audit(session, "stakeholder_interaction", "interview_answer", result)
        await self.persist_to_db(project_id, db)
        return result.data

    async def extract_requirements(self, project_id: str, user_id: str,
                                    text: str = "", source_type: str = "conversation", db=None) -> dict:
        """Extract structured requirements from actual interview text or input."""
        await self.sync_from_db(project_id, db)
        session = self._get_session(project_id)
        session["stage"] = "extraction"

        # If no explicit text provided, compile the entire conversation history!
        if not text and session.get("conversation_history"):
            formatted_turns = []
            for m in session["conversation_history"]:
                speaker = "Stakeholder" if m.get("role") in ("user", "stakeholder") else "Interviewer"
                body = m.get("content", "").strip()
                if body:
                    formatted_turns.append(f"{speaker}: {body}")
            text = "\n\n".join(formatted_turns)

        existing_ids = [r.get("requirement_id", "") for r in session["requirements"]]

        agent_input = AgentInput(
            task_id=str(uuid.uuid4()),
            agent_name="requirement_extraction",
            project_id=project_id,
            user_id=user_id,
            data={"text": text, "source_type": source_type, "existing_requirement_ids": existing_ids},
        )

        result = await self.agents["requirement_extraction"].execute(agent_input)
        if result.status == "error":
            err = "; ".join(result.issues) if result.issues else result.data.get("error", "Unknown extraction error")
            raise RuntimeError(f"Requirement extraction agent error: {err}")

        new_reqs = result.data.get("requirements", [])

        # Avoid duplicates by matching requirement statements
        existing_statements = {r.get("statement", "").strip().lower() for r in session["requirements"]}
        added = []
        for r in new_reqs:
            stmt = r.get("statement", "").strip().lower()
            if stmt not in existing_statements:
                session["requirements"].append(r)
                existing_statements.add(stmt)
                added.append(r)

        result.data["requirements"] = session["requirements"]
        result.data["count"] = len(session["requirements"])

        self._log_audit(session, "requirement_extraction", "extract", result)
        await self.persist_to_db(project_id, db, stage="extraction")
        return result.data

    async def run_analysis_pipeline(self, project_id: str, user_id: str, db=None) -> dict:
        """Run the full 7-stage analysis pipeline: clarification → classification → conflict →
        compliance → security → risk → validation."""
        await self.sync_from_db(project_id, db)
        session = self._get_session(project_id)
        requirements = session["requirements"]
        results = {}

        if not requirements:
            return {"error": "No requirements to analyse. Please complete the interview and extraction first."}

        # Stage 1: Clarification
        clarification = await self.agents["clarification"].execute(
            AgentInput(project_id=project_id, user_id=user_id,
                      data={"requirements": requirements})
        )
        results["clarification"] = clarification.data
        self._log_audit(session, "clarification", "analyse", clarification)

        # Stage 2: Classification
        classification = await self.agents["classification"].execute(
            AgentInput(project_id=project_id, user_id=user_id,
                      data={"requirements": requirements})
        )
        results["classification"] = classification.data
        self._log_audit(session, "classification", "analyse", classification)

        # Stage 3: Conflict Detection
        conflict = await self.agents["conflict_detection"].execute(
            AgentInput(project_id=project_id, user_id=user_id,
                      data={"requirements": requirements})
        )
        results["conflict_detection"] = conflict.data
        self._log_audit(session, "conflict_detection", "analyse", conflict)

        # Fetch project jurisdiction
        proj_jurisdiction = "US"
        if db:
            from models.project import Project
            p_res = await db.execute(select(Project).where(Project.id == project_id))
            p_obj = p_res.scalar_one_or_none()
            if p_obj and p_obj.jurisdiction:
                proj_jurisdiction = p_obj.jurisdiction

        # Stage 4: Compliance
        compliance = await self.agents["compliance"].execute(
            AgentInput(project_id=project_id, user_id=user_id,
                      data={"requirements": requirements, "jurisdiction": proj_jurisdiction})
        )
        results["compliance"] = compliance.data
        self._log_audit(session, "compliance", "analyse", compliance)

        # Stage 5: Security & Privacy
        security = await self.agents["security_privacy"].execute(
            AgentInput(project_id=project_id, user_id=user_id,
                      data={"requirements": requirements})
        )
        results["security"] = security.data
        self._log_audit(session, "security_privacy", "analyse", security)

        # Stage 6: Risk Analysis
        risk = await self.agents["risk_analysis"].execute(
            AgentInput(project_id=project_id, user_id=user_id,
                      data={"requirements": requirements,
                            "compliance_analysis": compliance.data.get("compliance_analysis", []),
                            "security_analysis": security.data.get("security_analysis", [])})
        )
        results["risk_analysis"] = risk.data
        self._log_audit(session, "risk_analysis", "analyse", risk)

        # Stage 7: Validation
        validation = await self.agents["validation"].execute(
            AgentInput(project_id=project_id, user_id=user_id,
                      data={"requirements": requirements})
        )
        results["validation"] = validation.data
        self._log_audit(session, "validation", "analyse", validation)

        session["analysis_results"] = results
        session["stage"] = "analysis"

        self._log_audit(session, "orchestrator", "analysis_pipeline_complete",
                        AgentOutput(agent_name="orchestrator", status="success",
                                    data={"stages": list(results.keys())}, confidence=0.92))

        await self.persist_to_db(project_id, db, stage="analysis")
        return results

    async def run_sdlc_analysis(self, project_id: str, user_id: str,
                                 factors: dict | None = None, db=None) -> dict:
        """Run SDLC selection analysis with deterministic multi-criteria scoring."""
        await self.sync_from_db(project_id, db)
        session = self._get_session(project_id)
        session["stage"] = "sdlc"

        agent_input = AgentInput(
            project_id=project_id, user_id=user_id,
            data={"requirements": session["requirements"], "factors": factors or {}},
        )

        result = await self.agents["sdlc_selection"].execute(agent_input)
        session["analysis_results"]["sdlc"] = result.data
        self._log_audit(session, "sdlc_selection", "analyse", result)

        await self.persist_to_db(project_id, db, stage="sdlc")
        return result.data

    analyse_sdlc = run_sdlc_analysis

    async def generate_srs(self, project_id: str, user_id: str,
                           project_name: str = "", project_desc: str = "",
                           jurisdiction: str = "US", approval_status: str = "pending",
                           db=None) -> dict:
        """Generate comprehensive IEEE 29148 SRS document (PDF, DOCX, JSON)."""
        await self.sync_from_db(project_id, db)
        session = self._get_session(project_id)
        session["stage"] = "srs"

        analysis = session.get("analysis_results", {})

        agent_input = AgentInput(
            project_id=project_id,
            user_id=user_id,
            data={
                "project_name": project_name or project_id,
                "project_description": project_desc,
                "jurisdiction": jurisdiction,
                "approval_status": approval_status,
                "requirements": session["requirements"],
                "compliance_analysis": analysis.get("compliance", {}).get("compliance_analysis", []),
                "security_analysis": analysis.get("security", {}).get("security_analysis", []),
                "risk_assessment": analysis.get("risk_analysis", {}).get("risk_assessment", []),
                "sdlc": analysis.get("sdlc", {}),
            },
        )

        result = await self.agents["documentation"].execute(agent_input)
        session["srs_result"] = result.data
        self._log_audit(session, "documentation", "generate_srs", result)

        # Auto-create pending approval request for SRS baseline
        await self.request_approval(
            project_id=project_id,
            user_id=user_id,
            approval_type="requirement_baseline",
            title=f"SRS Baseline Sign-Off: {project_name or project_id}",
            description="Formal IEEE 29148 Software Requirements Specification baseline awaiting stakeholder sign-off.",
            target_id=project_id,
            target_data={"version": "1.0", "requirements_count": len(session["requirements"])},
            db=db,
        )

        await self.persist_to_db(project_id, db, stage="srs")
        return result.data

    async def request_approval(self, project_id: str, user_id: str,
                                approval_type: str, title: str = "",
                                description: str = "", target_id: str = "",
                                target_data: dict = None, db=None) -> dict:
        """Create a human approval request in session and database."""
        await self.sync_from_db(project_id, db)
        session = self._get_session(project_id)

        agent_input = AgentInput(
            project_id=project_id, user_id=user_id,
            data={"approval_type": approval_type, "target_id": target_id,
                  "description": description, "target_data": target_data or {}},
        )

        result = await self.agents["human_approval"].execute(agent_input)
        app_req = result.data.get("approval_request", {})
        if title:
            app_req["title"] = title

        # Persist to database if db session provided
        if db is not None:
            try:
                from models.approval import ApprovalRequest
                from sqlalchemy import select

                # Check if identical pending approval already exists
                existing = await db.execute(
                    select(ApprovalRequest).where(
                        ApprovalRequest.project_id == project_id,
                        ApprovalRequest.request_type == approval_type,
                        ApprovalRequest.status == "pending"
                    )
                )
                if not existing.scalar_one_or_none():
                    db_approval = ApprovalRequest(
                        id=str(uuid.uuid4()),
                        project_id=project_id,
                        request_type=approval_type,
                        title=app_req.get("title", f"Approval: {approval_type}"),
                        description=description,
                        target_type="srs" if "baseline" in approval_type else "sdlc",
                        target_id=target_id or project_id,
                        target_data=target_data or {},
                        required_roles=app_req.get("required_roles", ["project_manager"]),
                        status="pending",
                        priority="high",
                    )
                    db.add(db_approval)
                    await db.flush()
                    app_req["id"] = db_approval.id
            except Exception as e:
                logger.error(f"Error persisting approval to DB: {e}")

        session["approval_requests"].append(app_req)
        self._log_audit(session, "human_approval", "create_approval_request", result)
        await self.persist_to_db(project_id, db)
        return app_req

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
            "analysis_results": session["analysis_results"],
            "has_srs": bool(session.get("srs_result")),
            "srs_result": session.get("srs_result"),
            "pending_approvals": len([a for a in session["approval_requests"]
                                      if a.get("status") == "pending"]),
            "audit_count": len(session["audit_trail"]),
        }

    def get_requirements(self, project_id: str) -> list:
        return self._get_session(project_id)["requirements"]

    def get_audit_trail(self, project_id: str) -> list:
        return self._get_session(project_id)["audit_trail"]

    def _log_audit(self, session: dict, agent_name: str, action: str, result: AgentOutput):
        session["audit_trail"].append({
            "agent": agent_name,
            "action": action,
            "status": result.status,
            "confidence": result.confidence,
            "issues": result.issues[:5] if result.issues else [],
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
