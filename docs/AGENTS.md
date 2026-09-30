# Agents

## Agent Registry (13 agents)

| Agent | Responsibility | Dependencies | Escalation |
|-------|---------------|-------------|-----------|
| **Coordinator** (Orchestrator) | Pipeline execution, session state, audit | None | — |
| **Stakeholder Interaction** | Adaptive interviews | None | Low confidence |
| **Requirement Extraction** | Extract from text/documents | Stakeholder | Missing text |
| **Clarification** | Detect ambiguity, generate questions | Extraction | — |
| **Classification** | Multi-label categorisation | Extraction | — |
| **Conflict Detection** | Contradictions, duplicates | Classification | Conflicts found |
| **Compliance** | Regulatory mapping (advisory) | Classification | Items needing review |
| **Security & Privacy** | Threat analysis, controls | Classification | High risk items |
| **Risk Analysis** | Business/technical/compliance risk | Compliance, Security | — |
| **Validation** | Quality checks (10 dimensions) | Compliance, Security, Conflict | — |
| **Documentation** | SRS, user stories, RTM generation | Validation | — |
| **SDLC Selection** | Deterministic scoring + LLM rationale | Risk Analysis | Always (requires approval) |
| **Human Approval** | Route decisions to required roles | None | Always |

## Agent Communication
All agents use structured `AgentInput` → `AgentOutput` schemas (Pydantic).
No uncontrolled free-form text between agents.

## Pipeline Order
```
Extraction → Clarification → Classification → Conflict Detection
→ Compliance → Security → Risk → Validation
→ (Documentation, SDLC — on demand)
→ Human Approval (when escalated)
```
