"""Pydantic schemas for all API models — typed, validated I/O."""
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, EmailStr
from typing import Optional


# ── Enums ──────────────────────────────────────────────

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "user"
    PROJECT_MANAGER = "user"
    BUSINESS_ANALYST = "user"
    ARCHITECT = "user"
    SECURITY_OFFICER = "user"
    COMPLIANCE_OFFICER = "user"
    STAKEHOLDER = "user"
    AUDITOR = "user"


class RequirementStatus(str, Enum):
    RAW = "raw"
    EXTRACTED = "extracted"
    NEEDS_CLARIFICATION = "needs_clarification"
    STRUCTURED = "structured"
    ANALYSED = "analysed"
    VALIDATED = "validated"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONFLICTED = "conflicted"
    SUPERSEDED = "superseded"
    CHANGED = "changed"


class RequirementCategory(str, Enum):
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    SECURITY = "security"
    PRIVACY = "privacy"
    REGULATORY = "regulatory"
    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    USABILITY = "usability"
    DATA = "data"
    INTEGRATION = "integration"
    AUDIT_REPORTING = "audit_reporting"
    OPERATIONAL = "operational"


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ApprovalType(str, Enum):
    REQUIREMENT_BASELINE = "requirement_baseline"
    REGULATORY_INTERPRETATION = "regulatory_interpretation"
    HIGH_RISK_SECURITY = "high_risk_security"
    STAKEHOLDER_CONFLICT = "stakeholder_conflict"
    ARCHITECTURE_CRITICAL = "architecture_critical"
    SDLC_SELECTION = "sdlc_selection"
    REQUIREMENT_CHANGE = "requirement_change"
    PRODUCTION_READINESS = "production_readiness"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    CANCELLED = "cancelled"


class ApprovalActionType(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"
    REQUEST_REGENERATION = "request_regeneration"


class DocumentType(str, Enum):
    POLICY = "policy"
    REGULATION = "regulation"
    REQUIREMENT = "requirement"
    INTERVIEW_TRANSCRIPT = "interview_transcript"
    MEETING_NOTES = "meeting_notes"
    API_SPEC = "api_spec"
    LEGACY_DOC = "legacy_doc"
    AUDIT_FINDING = "audit_finding"
    GENERAL = "general"


class UseCase(str, Enum):
    LOAN_PROCESSING = "loan_processing"
    DIGITAL_ONBOARDING = "digital_onboarding"
    PAYMENT_PROCESSING = "payment_processing"
    FRAUD_DETECTION = "fraud_detection"
    REGULATORY_REPORTING = "regulatory_reporting"
    INSURANCE = "insurance"
    INVESTMENT = "investment"
    DATA_ANALYTICS = "data_analytics"


# ── Auth Schemas ───────────────────────────────────────

class UserCreate(BaseModel):
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    role: Optional[str] = "user"
    organization: str = ""
    department: str = ""


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str = "user"
    organization: str = ""
    department: str = ""
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Project Schemas ────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=3)
    description: str = ""
    use_case: UseCase = UseCase.LOAN_PROCESSING
    jurisdiction: str = ""
    industry_segment: str = "banking"


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    use_case: str
    status: str
    current_stage: str = "interview"
    owner_id: str
    jurisdiction: str
    industry_segment: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Requirement Schemas ────────────────────────────────

class RequirementCreate(BaseModel):
    statement: str = Field(..., min_length=10)
    category: RequirementCategory = RequirementCategory.FUNCTIONAL
    source: str = ""
    source_type: str = "stakeholder"
    business_justification: str = ""
    priority: Priority = Priority.MEDIUM


class RequirementUpdate(BaseModel):
    statement: Optional[str] = None
    category: Optional[RequirementCategory] = None
    priority: Optional[Priority] = None
    business_justification: Optional[str] = None
    status: Optional[RequirementStatus] = None
    change_reason: str = ""


class RequirementResponse(BaseModel):
    id: str
    requirement_id: str
    project_id: str
    statement: str
    category: str
    subcategory: str
    source: str
    source_type: str
    business_justification: str
    priority: str
    dependencies: list
    assumptions: list
    acceptance_criteria: list
    applicable_regulations: list
    applicable_controls: list
    risks: list
    evidence: list
    confidence: float
    is_ambiguous: bool
    is_incomplete: bool
    is_conflicting: bool
    is_duplicate: bool
    quality_issues: list
    status: str
    version: int
    is_current: bool
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None

    class Config:
        from_attributes = True


# ── Document Schemas ───────────────────────────────────

class DocumentResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    title: str
    doc_type: str
    jurisdiction: str
    status: str
    chunk_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Approval Schemas ───────────────────────────────────

class ApprovalRequestCreate(BaseModel):
    request_type: ApprovalType
    title: str
    description: str = ""
    target_type: str = ""
    target_id: str = ""
    target_data: dict = {}
    required_roles: list[str] = []
    priority: Priority = Priority.MEDIUM


class ApprovalActionCreate(BaseModel):
    action: ApprovalActionType
    comments: str = ""
    modifications: dict = {}


class ApprovalRequestResponse(BaseModel):
    id: str
    project_id: str
    request_type: str
    title: str
    description: str
    context: dict
    target_type: str
    target_id: str
    required_roles: list
    status: str
    priority: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    actions: list = []

    class Config:
        from_attributes = True


# ── Stakeholder Interview Schemas ──────────────────────

class InterviewMessage(BaseModel):
    role: str  # "system", "assistant", "user"
    content: str
    timestamp: Optional[datetime] = None


class InterviewStartRequest(BaseModel):
    project_id: str
    stakeholder_role: str = "business_analyst"
    context: str = ""


class InterviewResponse(BaseModel):
    session_id: str
    question: str
    topics_covered: list[str] = []
    topics_remaining: list[str] = []
    progress_pct: float = 0.0


class InterviewAnswerRequest(BaseModel):
    session_id: str
    answer: str


# ── SDLC Schemas ───────────────────────────────────────

class SDLCFactors(BaseModel):
    requirement_stability: float = Field(0.5, ge=0, le=1)
    regulatory_criticality: float = Field(0.5, ge=0, le=1)
    security_risk: float = Field(0.5, ge=0, le=1)
    complexity: float = Field(0.5, ge=0, le=1)
    system_size: float = Field(0.5, ge=0, le=1)
    legacy_dependence: float = Field(0.5, ge=0, le=1)
    change_frequency: float = Field(0.5, ge=0, le=1)
    continuous_delivery: float = Field(0.5, ge=0, le=1)
    stakeholder_availability: float = Field(0.5, ge=0, le=1)
    testing_requirements: float = Field(0.5, ge=0, le=1)
    budget_schedule_pressure: float = Field(0.5, ge=0, le=1)
    formal_verification: float = Field(0.5, ge=0, le=1)
    failure_consequences: float = Field(0.5, ge=0, le=1)


class SDLCRecommendation(BaseModel):
    recommended_model: str
    confidence: float
    factors: dict
    scores: dict  # model -> score
    rationale: str
    alternatives: list[dict]
    requires_approval: bool = True


# ── Artefact Schemas ───────────────────────────────────

class ArtefactRequest(BaseModel):
    artefact_type: str
    # srs, user_stories, use_cases, acceptance_criteria,
    # process_workflows, data_requirements, interface_requirements,
    # threat_risk_register, compliance_matrix, rtm,
    # assumptions_register, open_issues, sdlc_workflow
    project_id: str
    requirement_ids: list[str] = []  # empty = all project requirements
    format: str = "markdown"  # markdown, json


class ArtefactResponse(BaseModel):
    id: str
    artefact_type: str
    title: str
    content: str
    format: str
    source_requirements: list[str]
    evidence_citations: list[dict]
    created_at: datetime


# ── Agent Communication Schemas ────────────────────────

class AgentInput(BaseModel):
    """Standard input to any agent."""
    task_id: str = ""
    agent_name: str = ""
    data: dict = {}
    context: dict = {}
    project_id: str = ""
    user_id: str = ""


class AgentOutput(BaseModel):
    """Standard output from any agent."""
    agent_name: str
    status: str  # success, error, needs_human_review, escalated
    data: dict = {}
    citations: list[dict] = []
    confidence: float = 0.0
    issues: list[str] = []
    next_actions: list[str] = []
    audit_entry: dict = {}
