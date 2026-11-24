"""AIFRE — Agentic AI Financial Requirements Engineering System.

Main FastAPI application entry point.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    logger.info("AIFRE starting up...")
    await init_db()
    await seed_knowledge_base()
    logger.info(f"AIFRE ready — LLM provider: {settings.LLM_PROVIDER}")
    yield
    logger.info("AIFRE shutting down...")


app = FastAPI(
    title="AIFRE — AI Financial Requirements Engineering",
    description="Agentic AI platform for financial requirements engineering with "
                "adaptive interviews, RAG-grounded analysis, compliance checking, "
                "SDLC selection, and human approval workflows.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"^https?://.*$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register API routers ──────────────────────────────

from api.auth import router as auth_router
from api.projects import router as projects_router
from api.requirements import router as requirements_router
from api.documents import router as documents_router
from api.approvals import router as approvals_router
from api.sdlc import router as sdlc_router
from api.srs import router as srs_router

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(requirements_router)
app.include_router(documents_router)
app.include_router(approvals_router, prefix="/api")
app.include_router(approvals_router)  # Also supports /projects/{id}/approvals directly
app.include_router(sdlc_router)
app.include_router(srs_router)


# ── Evaluation endpoint ───────────────────────────────

from evaluation.framework import EvaluationFramework

@app.post("/api/evaluation/run", tags=["evaluation"])
async def run_evaluation():
    """Run the evaluation framework against the system."""
    from agents.orchestrator import get_orchestrator
    framework = EvaluationFramework()
    results = await framework.run_evaluation(get_orchestrator())
    return results


@app.get("/api/evaluation/test-cases", tags=["evaluation"])
async def get_test_cases():
    """Get all evaluation test cases."""
    framework = EvaluationFramework()
    return framework.get_test_cases()


# ── Health check ───────────────────────────────────────

@app.get("/api/health", tags=["system"])
async def health_check():
    from rag.pipeline import get_collection_stats
    from llm.gateway import get_llm_provider
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_info": get_llm_provider().get_model_info(),
        "vector_store": get_collection_stats(),
    }


# ── Knowledge base seeding ────────────────────────────

async def seed_knowledge_base():
    """Seed the knowledge base with loan processing domain knowledge."""
    from rag.pipeline import add_documents, get_collection_stats

    stats = get_collection_stats()
    if stats.get("count", 0) > 0:
        logger.info(f"Knowledge base already seeded ({stats['count']} items)")
        return

    logger.info("Seeding knowledge base with loan processing domain knowledge...")

    knowledge_items = [
        {
            "text": "Know Your Customer (KYC) regulations require financial institutions to verify the identity of their clients. This includes collecting government-issued identification, proof of address, and conducting due diligence on the customer's background. Enhanced due diligence is required for high-risk customers.",
            "metadata": {"category": "regulation", "source": "KYC Framework", "jurisdiction": "general", "applicability": "loan_processing,digital_onboarding"},
        },
        {
            "text": "Anti-Money Laundering (AML) directives require financial institutions to monitor transactions for suspicious activity, report suspicious transactions to authorities, maintain records of customer transactions for a minimum of 5 years, and implement risk-based controls proportional to the assessed risk level.",
            "metadata": {"category": "regulation", "source": "AML Directives", "jurisdiction": "general", "applicability": "loan_processing,payment_processing"},
        },
        {
            "text": "Data protection principles require that personal data be processed lawfully, fairly and transparently; collected for specified, explicit and legitimate purposes; adequate, relevant and limited to what is necessary; accurate and kept up to date; stored only as long as necessary; processed with appropriate security measures.",
            "metadata": {"category": "regulation", "source": "Data Protection Act", "jurisdiction": "general", "applicability": "all"},
        },
        {
            "text": "Consumer credit regulations require lenders to assess creditworthiness before granting credit, provide clear pre-contractual information, allow a cooling-off period, ensure fair treatment of borrowers in financial difficulty, and maintain transparent pricing without hidden fees.",
            "metadata": {"category": "regulation", "source": "Consumer Credit Act", "jurisdiction": "general", "applicability": "loan_processing"},
        },
        {
            "text": "Information security standards for financial systems require: access control with role-based permissions and multi-factor authentication; encryption of data at rest (AES-256) and in transit (TLS 1.3); security monitoring and incident response; vulnerability management and penetration testing; secure software development lifecycle.",
            "metadata": {"category": "security_standard", "source": "Financial Security Standards", "jurisdiction": "general", "applicability": "all"},
        },
        {
            "text": "Loan processing workflow: Application intake → Identity verification (KYC) → Credit assessment → Risk evaluation → Loan structuring → Approval/rejection → Documentation → Disbursement → Servicing. Each stage requires audit logging and may require human approval for high-value or high-risk decisions.",
            "metadata": {"category": "process", "source": "Banking Operations Guide", "jurisdiction": "general", "applicability": "loan_processing"},
        },
        {
            "text": "Credit risk assessment factors include: credit history and score, income stability and verification, debt-to-income ratio, collateral valuation, employment history, existing obligations, loan-to-value ratio, and industry/sector risk. Automated scoring must be explainable and free from discriminatory bias.",
            "metadata": {"category": "process", "source": "Credit Risk Management Framework", "jurisdiction": "general", "applicability": "loan_processing"},
        },
        {
            "text": "Prudential lending standards limit exposure per borrower, require adequate capital reserves, mandate stress testing of loan portfolios, and require board-level oversight of lending policies. Material changes to lending criteria require regulatory notification.",
            "metadata": {"category": "regulation", "source": "Prudential Standards", "jurisdiction": "general", "applicability": "loan_processing"},
        },
        {
            "text": "Record retention requirements for financial institutions: Customer identification records — minimum 5 years after relationship ends. Transaction records — minimum 7 years. Loan documentation — life of loan plus 7 years. Audit reports — minimum 10 years. Regulatory correspondence — minimum 7 years.",
            "metadata": {"category": "regulation", "source": "Record Retention Guidelines", "jurisdiction": "general", "applicability": "all"},
        },
        {
            "text": "SDLC selection guidelines for financial systems: High regulatory burden favours V-Model or hybrid approaches with formal verification gates. Rapidly evolving requirements favour Agile with compliance sprints. Critical security requirements favour DevSecOps. Most financial projects benefit from hybrid approaches combining Agile flexibility with V-Model verification rigour.",
            "metadata": {"category": "sdlc_rule", "source": "SDLC Selection Guide", "jurisdiction": "general", "applicability": "all"},
        },
    ]

    texts = [item["text"] for item in knowledge_items]
    metadatas = [item["metadata"] for item in knowledge_items]

    try:
        add_documents(texts, metadatas)
        logger.info(f"Seeded {len(texts)} knowledge items")
    except Exception as e:
        logger.warning(f"Could not seed knowledge base (offline/fallback): {e}")


# ── Run server ─────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
