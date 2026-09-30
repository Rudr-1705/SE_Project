"""Base agent — defines responsibility, I/O, tools, permissions, validation, escalation."""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from schemas.models import AgentInput, AgentOutput
from llm.gateway import LLMGateway
from security.sanitization import detect_prompt_injection, sanitize_input
import uuid
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base for all specialised agents.

    Every agent has:
    - name, responsibility, description
    - defined input/output schemas
    - allowed tools and permissions
    - dependencies on other agents
    - validation logic
    - escalation conditions
    """

    name: str = "base"
    responsibility: str = ""
    required_permissions: list[str] = []
    allowed_tools: list[str] = []
    dependencies: list[str] = []
    max_retries: int = 2

    def __init__(self):
        self.llm = LLMGateway()
        self.run_id = str(uuid.uuid4())

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """Main entry — validates input, checks for injection, runs agent, validates output."""
        try:
            # 1. Sanitize input
            sanitized_data = self._sanitize_input(agent_input)

            # 2. Check for prompt injection in text fields
            injection_check = self._check_injection(sanitized_data)
            if injection_check:
                return AgentOutput(
                    agent_name=self.name,
                    status="error",
                    data={"injection_detected": True, "patterns": injection_check},
                    issues=["Potential prompt injection detected in input"],
                    confidence=0.0,
                    audit_entry=self._audit_entry("injection_blocked", agent_input),
                )

            # 3. Validate input
            validation_errors = self.validate_input(sanitized_data)
            if validation_errors:
                return AgentOutput(
                    agent_name=self.name,
                    status="error",
                    data={"validation_errors": validation_errors},
                    issues=validation_errors,
                    confidence=0.0,
                    audit_entry=self._audit_entry("validation_failed", agent_input),
                )

            # 4. Run the agent logic
            result = await self.run(sanitized_data)

            # 5. Check escalation conditions
            if self.should_escalate(result):
                result.status = "needs_human_review"
                result.next_actions.append("human_review_required")

            # 6. Attach audit entry
            result.audit_entry = self._audit_entry("completed", agent_input, result)

            return result

        except Exception as e:
            logger.error(f"Agent {self.name} failed: {e}", exc_info=True)
            return AgentOutput(
                agent_name=self.name,
                status="error",
                data={"error": str(e)},
                issues=[f"Agent execution failed: {str(e)}"],
                confidence=0.0,
                audit_entry=self._audit_entry("error", agent_input),
            )

    @abstractmethod
    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """Core agent logic — implemented by each specialised agent."""
        ...

    def validate_input(self, agent_input: AgentInput) -> list[str]:
        """Override to add input validation. Return list of error messages."""
        return []

    def should_escalate(self, output: AgentOutput) -> bool:
        """Override to define escalation conditions."""
        if output.confidence < 0.5:
            return True
        return False

    def _sanitize_input(self, agent_input: AgentInput) -> AgentInput:
        """Sanitize all text fields in agent input."""
        sanitized = agent_input.model_copy()
        for key, value in sanitized.data.items():
            if isinstance(value, str):
                sanitized.data[key] = sanitize_input(value)
        return sanitized

    def _check_injection(self, agent_input: AgentInput) -> list[str]:
        """Check all text fields for prompt injection."""
        all_patterns = []
        for key, value in agent_input.data.items():
            if isinstance(value, str):
                is_suspicious, patterns = detect_prompt_injection(value)
                if is_suspicious:
                    all_patterns.extend(patterns)
        if agent_input.context:
            for key, value in agent_input.context.items():
                if isinstance(value, str):
                    is_suspicious, patterns = detect_prompt_injection(value)
                    if is_suspicious:
                        all_patterns.extend(patterns)
        return all_patterns

    def _audit_entry(self, action: str, agent_input: AgentInput,
                     output: AgentOutput | None = None) -> dict:
        """Create audit log entry for this agent execution."""
        entry = {
            "agent_name": self.name,
            "run_id": self.run_id,
            "action": action,
            "project_id": agent_input.project_id,
            "user_id": agent_input.user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model_info": self.llm.provider.get_model_info(),
        }
        if output:
            entry["confidence"] = output.confidence
            entry["status"] = output.status
            entry["issues_count"] = len(output.issues)
        return entry
