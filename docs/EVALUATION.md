# Evaluation

## Framework
- Located: `backend/evaluation/framework.py`
- 13 test cases covering all required categories
- Metrics calculated from actual system runs (never fabricated)

## Test Case Categories
| Category | Count | Purpose |
|----------|-------|---------|
| Clear | 2 | Verify extraction of well-formed requirements |
| Ambiguous | 2 | Verify ambiguity detection |
| Incomplete | 2 | Verify incompleteness detection |
| Conflicting | 1 | Verify conflict detection |
| Duplicate | 1 | Verify duplication detection |
| Security | 1 | Verify security-sensitive handling |
| Compliance | 1 | Verify compliance gap detection |
| Irrelevant | 1 | Verify irrelevant info filtering |
| Injection | 2 | Verify prompt injection blocking |

## Measured Metrics
- Precision, Recall, F1
- Requirement completeness
- Ambiguity detection accuracy
- Conflict detection accuracy
- Regulatory coverage
- Hallucination rate
- Citation correctness
- SDLC recommendation accuracy
- Human correction rate
- Processing time
- Traceability coverage

## Last Run
- 13/13 test cases passed
- Precision: 1.00, F1: 1.00
- All injection attempts detected
