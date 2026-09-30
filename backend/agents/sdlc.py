"""SDLC Selection Agent — deterministic rules + multi-criteria analysis + LLM explanation."""
import json
from agents.base import BaseAgent
from schemas.models import AgentInput, AgentOutput

# ── Deterministic SDLC scoring rules ──────────────────
# Each model has a base scoring function based on project factors
SDLC_MODELS = {
    "waterfall": {"display": "Waterfall", "weights": {
        "requirement_stability": 0.20, "regulatory_criticality": 0.10,
        "formal_verification": 0.15, "change_frequency": -0.20,
        "stakeholder_availability": -0.05, "continuous_delivery": -0.15,
    }},
    "v_model": {"display": "V-Model", "weights": {
        "requirement_stability": 0.15, "regulatory_criticality": 0.15,
        "formal_verification": 0.20, "testing_requirements": 0.15,
        "failure_consequences": 0.10, "change_frequency": -0.15,
    }},
    "spiral": {"display": "Spiral", "weights": {
        "security_risk": 0.15, "complexity": 0.15,
        "failure_consequences": 0.15, "budget_schedule_pressure": -0.10,
        "change_frequency": 0.10,
    }},
    "agile": {"display": "Agile", "weights": {
        "change_frequency": 0.20, "stakeholder_availability": 0.15,
        "continuous_delivery": 0.10, "requirement_stability": -0.15,
        "formal_verification": -0.10,
    }},
    "devsecops": {"display": "DevSecOps", "weights": {
        "continuous_delivery": 0.20, "security_risk": 0.15,
        "change_frequency": 0.10, "testing_requirements": 0.10,
        "formal_verification": -0.05,
    }},
    "hybrid_agile_vmodel": {"display": "Agile-V-Model Hybrid", "weights": {
        "regulatory_criticality": 0.15, "change_frequency": 0.10,
        "testing_requirements": 0.15, "security_risk": 0.10,
        "stakeholder_availability": 0.10, "formal_verification": 0.10,
        "failure_consequences": 0.10,
    }},
}

SYSTEM_PROMPT = """You are an SDLC methodology expert for financial systems.
Given project factors and model scores, provide a detailed rationale for the recommendation.
Explain WHY the recommended model fits, its trade-offs, and alternatives.
This is advisory — final SDLC choice requires approval by project manager, architect,
security team and compliance officer.
Respond with JSON: rationale (string), trade_offs (array), implementation_notes (string)."""


def score_sdlc_models(factors: dict) -> dict:
    """Deterministic multi-criteria scoring of SDLC models."""
    scores = {}
    for model_name, model_config in SDLC_MODELS.items():
        score = 0.5  # base score
        for factor, weight in model_config["weights"].items():
            factor_value = factors.get(factor, 0.5)
            score += weight * factor_value
        scores[model_name] = max(0.0, min(1.0, score))
    return scores


class SDLCAgent(BaseAgent):
    name = "sdlc_selection"
    responsibility = "Analyse project factors and recommend SDLC approach"
    required_permissions = ["agents.execute"]
    allowed_tools = ["llm_generate"]
    dependencies = ["risk_analysis"]

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        factors = agent_input.data.get("factors", {})
        requirements = agent_input.data.get("requirements", [])

        # If no factors provided, derive from requirements
        if not factors:
            factors = self._derive_factors(requirements)

        # 1. Deterministic scoring
        scores = score_sdlc_models(factors)

        # 2. Rank models
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        recommended = ranked[0]
        alternatives = ranked[1:3]

        # 3. Get LLM explanation
        prompt = f"""Given these SDLC model scores for a financial system:
{json.dumps({k: round(v, 3) for k, v in scores.items()}, indent=2)}

Project factors:
{json.dumps({k: round(v, 3) for k, v in factors.items()}, indent=2)}

The recommended model is: {SDLC_MODELS[recommended[0]]['display']} (score: {recommended[1]:.3f})
Alternatives: {', '.join(f"{SDLC_MODELS[a[0]]['display']} ({a[1]:.3f})" for a in alternatives)}

Provide a detailed rationale explaining why this model fits, its trade-offs, and implementation notes.
This recommendation requires approval by project manager, architect, security and compliance.
Respond as JSON."""

        result = await self.llm.generate_structured(prompt, SYSTEM_PROMPT)
        response_data = result["data"]

        return AgentOutput(
            agent_name=self.name, status="success",
            data={
                "recommended_model": recommended[0],
                "display_name": SDLC_MODELS[recommended[0]]["display"],
                "recommended_score": round(recommended[1], 3),
                "scores": {k: round(v, 3) for k, v in scores.items()},
                "factors": factors,
                "rationale": response_data.get("rationale", ""),
                "trade_offs": response_data.get("trade_offs", []),
                "implementation_notes": response_data.get("implementation_notes", ""),
                "alternatives": [{"model": a[0], "display": SDLC_MODELS[a[0]]["display"],
                                  "score": round(a[1], 3)} for a in alternatives],
                "requires_approval": True,
                "required_approvers": ["project_manager", "architect", "security_officer", "compliance_officer"],
            },
            confidence=round(recommended[1], 3),
        )

    def _derive_factors(self, requirements: list) -> dict:
        """Derive SDLC factors from requirements characteristics."""
        n = max(len(requirements), 1)
        sec_count = sum(1 for r in requirements if r.get("category") in ("security", "privacy"))
        reg_count = sum(1 for r in requirements if r.get("applicable_regulations"))
        critical_count = sum(1 for r in requirements if r.get("priority") == "critical")

        return {
            "requirement_stability": 0.6,
            "regulatory_criticality": min(1.0, reg_count / n + 0.3),
            "security_risk": min(1.0, sec_count / n + 0.3),
            "complexity": min(1.0, n / 50 + 0.3),
            "system_size": min(1.0, n / 100 + 0.3),
            "legacy_dependence": 0.4,
            "change_frequency": 0.5,
            "continuous_delivery": 0.6,
            "stakeholder_availability": 0.7,
            "testing_requirements": min(1.0, critical_count / n + 0.5),
            "budget_schedule_pressure": 0.5,
            "formal_verification": min(1.0, reg_count / n + 0.4),
            "failure_consequences": min(1.0, critical_count / n + 0.5),
        }
