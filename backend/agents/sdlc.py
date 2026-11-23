"""SDLC Selection Agent — deterministic rules + multi-criteria analysis + LLM explanation."""
import json
from agents.base import BaseAgent
from schemas.models import AgentInput, AgentOutput

# ── 6 Evaluated SDLC Methodologies & Weights ──────────
SDLC_MODELS = {
    "hybrid_agile_vmodel": {
        "display": "Agile-V-Model Hybrid",
        "description": "Combines iterative sprint velocity for client workflows with rigorous V-Model verification for regulatory compliance and auditability.",
        "pros": ["Iterative stakeholder feedback", "Formal verification gateways", "Robust audit trails for regulators"],
        "cons": ["Requires dual-track governance", "Higher documentation overhead than pure Agile"],
        "weights": {
            "regulatory_criticality": 0.22,
            "testing_requirements": 0.20,
            "security_risk": 0.18,
            "formal_verification": 0.16,
            "change_frequency": 0.12,
            "stakeholder_availability": 0.12,
            "failure_consequences": 0.15,
        },
        "penalties": {
            "budget_schedule_pressure": 0.10,
        }
    },
    "devsecops": {
        "display": "DevSecOps",
        "description": "Integrates automated security testing (SAST/DAST) and compliance-as-code directly into continuous integration/delivery pipelines.",
        "pros": ["Continuous automated security checks", "Rapid deployment cadence", "Immediate vulnerability detection"],
        "cons": ["Demands mature CI/CD infrastructure", "Toolchain complexity"],
        "weights": {
            "continuous_delivery": 0.25,
            "security_risk": 0.22,
            "testing_requirements": 0.18,
            "change_frequency": 0.15,
            "stakeholder_availability": 0.10,
        },
        "penalties": {
            "legacy_dependence": 0.20,
            "formal_verification": 0.10,
        }
    },
    "v_model": {
        "display": "V-Model",
        "description": "Rigorous sequential engineering model where each development phase is strictly paired with an equivalent validation and verification phase.",
        "pros": ["High discipline and defect prevention", "Strict traceability", "Ideal for formal statutory sign-offs"],
        "cons": ["Rigid change resistance", "Late software visibility for end-users"],
        "weights": {
            "formal_verification": 0.25,
            "regulatory_criticality": 0.22,
            "testing_requirements": 0.20,
            "requirement_stability": 0.18,
            "failure_consequences": 0.15,
        },
        "penalties": {
            "change_frequency": 0.25,
            "continuous_delivery": 0.20,
        }
    },
    "spiral": {
        "display": "Spiral",
        "description": "Risk-driven lifecycle model emphasizing iterative risk assessment, prototyping, and stakeholder milestone reviews.",
        "pros": ["Superior architectural risk mitigation", "Early identification of operational bottlenecks", "Adaptive scoping"],
        "cons": ["High governance overhead", "Requires specialized risk analysts"],
        "weights": {
            "security_risk": 0.24,
            "complexity": 0.22,
            "failure_consequences": 0.20,
            "change_frequency": 0.14,
        },
        "penalties": {
            "budget_schedule_pressure": 0.20,
            "continuous_delivery": 0.15,
        }
    },
    "agile": {
        "display": "Agile (Scrum / Kanban)",
        "description": "Dynamic, iterative framework focused on rapid customer value delivery, continuous adaptation, and self-organizing cross-functional teams.",
        "pros": ["Fast time to market", "Flexible to evolving requirements", "High user collaboration"],
        "cons": ["Audit trails can fragment without strict tooling", "Harder to prove formal upfront compliance"],
        "weights": {
            "change_frequency": 0.28,
            "stakeholder_availability": 0.22,
            "continuous_delivery": 0.20,
        },
        "penalties": {
            "regulatory_criticality": 0.22,
            "formal_verification": 0.22,
            "failure_consequences": 0.15,
        }
    },
    "waterfall": {
        "display": "Waterfall",
        "description": "Classical linear-sequential lifecycle with discrete gated phases: requirements, design, implementation, verification, and maintenance.",
        "pros": ["Simple, structured milestones", "Comprehensive upfront specifications", "Clear deadline projections"],
        "cons": ["Inflexible to mid-flight change", "Testing occurs late in the project lifecycle"],
        "weights": {
            "requirement_stability": 0.25,
            "formal_verification": 0.20,
            "regulatory_criticality": 0.15,
        },
        "penalties": {
            "change_frequency": 0.30,
            "continuous_delivery": 0.25,
            "stakeholder_availability": 0.10,
        }
    },
}

SYSTEM_PROMPT = """You are an SDLC methodology expert for financial systems and regulated banking software.
Given project factors and model scores, provide a detailed rationale for the recommendation.
Explain WHY the recommended model fits, its trade-offs, and alternatives.
This is advisory — final SDLC choice requires approval by project manager, architect,
security team and compliance officer.
Respond with JSON: rationale (string), trade_offs (array of strings), implementation_notes (string)."""


def score_sdlc_models(factors: dict) -> dict:
    """Deterministic multi-criteria scoring of SDLC models with normalized weights and penalties."""
    scores = {}
    for model_name, model_config in SDLC_MODELS.items():
        weights = model_config.get("weights", {})
        penalties = model_config.get("penalties", {})
        
        pos_weight_sum = sum(weights.values())
        weighted_sum = 0.0
        penalty_sum = 0.0

        for factor, weight in weights.items():
            factor_val = float(factors.get(factor, 0.5))
            weighted_sum += weight * factor_val

        for factor, pen_weight in penalties.items():
            factor_val = float(factors.get(factor, 0.5))
            penalty_sum += pen_weight * factor_val

        raw_score = (weighted_sum / pos_weight_sum) if pos_weight_sum > 0 else 0.5
        adjusted_score = raw_score - (penalty_sum * 0.3)
        score = max(0.18, min(0.96, adjusted_score))
        scores[model_name] = round(score, 3)

    return scores


class SDLCAgent(BaseAgent):
    name = "sdlc_selection"
    responsibility = "Analyse project factors and recommend SDLC approach"
    required_permissions = ["agents.execute"]
    allowed_tools = ["llm_generate"]
    dependencies = ["risk_analysis"]

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        input_factors = agent_input.data.get("factors", {})
        requirements = agent_input.data.get("requirements", [])
        analysis_results = agent_input.data.get("analysis_results", {})

        # Derive factors grounded in actual requirements and multi-agent analysis findings
        derived_factors = self._derive_factors(requirements, analysis_results)
        
        # Merge factors: preserve derived criteria while incorporating input metadata
        factors = {**derived_factors}
        for k, v in input_factors.items():
            if isinstance(v, (int, float)):
                factors[k] = float(v)
            else:
                factors[k] = v

        # 1. Deterministic scoring
        scores = score_sdlc_models(factors)

        # 2. Rank models
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        recommended = ranked[0]
        alternatives = ranked[1:4]

        # 3. Model breakdown catalog with pros/cons/explanations
        evaluated_models = []
        for model_id, score_val in ranked:
            cfg = SDLC_MODELS[model_id]
            evaluated_models.append({
                "model": model_id,
                "display_name": cfg["display"],
                "score": round(score_val, 3),
                "is_recommended": (model_id == recommended[0]),
                "description": cfg["description"],
                "pros": cfg["pros"],
                "cons": cfg["cons"],
            })

        # 4. LLM explanation & rationale
        prompt = f"""Evaluate these 6 SDLC methodology fitness scores for a financial application:
{json.dumps({k: round(v, 3) if isinstance(v, (int, float)) else v for k, v in scores.items()}, indent=2)}

Project factors:
{json.dumps({k: round(v, 3) if isinstance(v, (int, float)) else v for k, v in factors.items()}, indent=2)}

The recommended model is: {SDLC_MODELS[recommended[0]]['display']} (score: {recommended[1]:.3f})
Alternatives: {', '.join(f"{SDLC_MODELS[a[0]]['display']} ({a[1]:.3f})" for a in alternatives)}

Provide:
1. Rationale justifying why {SDLC_MODELS[recommended[0]]['display']} best balances regulatory compliance and delivery velocity.
2. 3-4 key lifecycle trade-offs.
3. Implementation notes for engineering leadership.
Respond as JSON with keys: rationale, trade_offs, implementation_notes."""

        try:
            result = await self.llm.generate_structured(prompt, SYSTEM_PROMPT)
            response_data = result.get("data", {})
        except Exception:
            response_data = {}

        default_rationale = (
            f"The {SDLC_MODELS[recommended[0]]['display']} is recommended with a {round(recommended[1] * 100)}% fitness match. "
            f"This methodology was selected because the project requires stringent statutory compliance and auditability "
            f"while benefiting from iterative development cycles for user interfaces and external API integration."
        )

        default_tradeoffs = [
            f"Increased formal verification documentation to satisfy statutory compliance ({factors.get('jurisdiction', 'Financial Jurisdiction')})",
            "Sprint velocity is moderated by mandatory stage-gate security and compliance reviews",
            "Requires automated regression and compliance test suites to prevent late-cycle defect discovery"
        ]

        rationale = response_data.get("rationale") or default_rationale
        trade_offs = response_data.get("trade_offs") or default_tradeoffs
        impl_notes = response_data.get("implementation_notes") or "Establish automated CI/CD security scanning alongside formal stakeholder sign-offs."

        return AgentOutput(
            agent_name=self.name, status="success",
            data={
                "recommended_model": recommended[0],
                "recommended_framework": SDLC_MODELS[recommended[0]]["display"],
                "display_name": SDLC_MODELS[recommended[0]]["display"],
                "recommended_score": round(recommended[1], 3),
                "scores": {k: round(v, 3) for k, v in scores.items()},
                "factors": factors,
                "rationale": rationale,
                "trade_offs": trade_offs,
                "implementation_notes": impl_notes,
                "evaluated_models": evaluated_models,
                "alternatives": [{"model": a[0], "display": SDLC_MODELS[a[0]]["display"],
                                  "score": round(a[1], 3)} for a in alternatives],
                "requires_approval": True,
                "required_approvers": ["project_manager", "lead_architect", "security_officer", "compliance_officer"],
            },
            confidence=round(recommended[1], 3),
        )

    def _derive_factors(self, requirements: list, analysis_results: dict = None) -> dict:
        """Derive SDLC factors from requirements and actual multi-agent analysis findings."""
        analysis_results = analysis_results or {}
        n = max(len(requirements), 1)

        # Requirements analysis
        sec_reqs = sum(1 for r in requirements if "sec" in str(r.get("category", "")).lower() or "priv" in str(r.get("category", "")).lower())
        reg_reqs = sum(1 for r in requirements if r.get("applicable_regulations") or "regulatory" in str(r.get("category", "")).lower())
        crit_reqs = sum(1 for r in requirements if str(r.get("priority", "")).lower() in ("critical", "high"))
        ambig_reqs = sum(1 for r in requirements if r.get("is_ambiguous"))

        # Agent outputs
        comp_data = analysis_results.get("compliance", {})
        comp_items = comp_data.get("compliance_analysis", [])
        mandatory_reviews = sum(1 for c in comp_items if c.get("approval_required"))

        sec_data = analysis_results.get("security", {})
        high_risk_sec = sec_data.get("high_risk_count", 0)

        risk_data = analysis_results.get("risk_analysis", {})
        risk_items = risk_data.get("risk_assessment", [])
        high_critical_risks = sum(1 for rk in risk_items if str(rk.get("risk_level", "")).lower() in ("critical", "high"))

        val_data = analysis_results.get("validation", {}).get("validation_results", {})
        testability = float(val_data.get("testability", 0.75))
        traceability = float(val_data.get("traceability", 0.70))

        reg_crit = max(0.40, min(0.95, 0.45 + (reg_reqs / n) * 0.30 + (mandatory_reviews * 0.05)))
        sec_risk = max(0.40, min(0.95, 0.40 + (sec_reqs / n) * 0.30 + (high_risk_sec * 0.04) + (high_critical_risks * 0.04)))
        formal_ver = max(0.45, min(0.95, 0.50 + (reg_crit * 0.25) + (traceability * 0.15)))
        test_reqs = max(0.50, min(0.95, 0.45 + (crit_reqs / n) * 0.30 + (testability * 0.20)))
        fail_conseq = max(0.40, min(0.95, 0.45 + (crit_reqs / n) * 0.30 + (high_critical_risks * 0.05)))
        req_stability = max(0.30, min(0.85, 0.85 - (ambig_reqs / n) * 0.40))
        complexity = max(0.40, min(0.95, 0.40 + (n / 25.0) * 0.35 + (high_critical_risks * 0.05)))

        return {
            "requirement_stability": round(req_stability, 2),
            "regulatory_criticality": round(reg_crit, 2),
            "security_risk": round(sec_risk, 2),
            "complexity": round(complexity, 2),
            "system_size": round(max(0.3, min(0.9, (n / 35.0) * 0.5 + 0.3)), 2),
            "legacy_dependence": 0.40,
            "change_frequency": 0.55,
            "continuous_delivery": 0.65,
            "stakeholder_availability": 0.75,
            "testing_requirements": round(test_reqs, 2),
            "budget_schedule_pressure": 0.45,
            "formal_verification": round(formal_ver, 2),
            "failure_consequences": round(fail_conseq, 2),
        }
