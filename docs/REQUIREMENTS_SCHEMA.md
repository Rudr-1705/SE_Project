# Requirement Schema

## Canonical Requirement Object

```python
id                     # UUID
requirement_id         # Human-readable: FR-LOAN-001, NFR-SEC-003
project_id             # FK to Project
statement              # The requirement text
category               # functional, security, privacy, regulatory, performance, etc.
subcategory            # identity_verification, encryption, etc.
source                 # Stakeholder name / document ref
source_type            # stakeholder, document, system
business_justification # Why this requirement exists
priority               # critical, high, medium, low
dependencies           # List of requirement IDs
assumptions            # List of assumptions
acceptance_criteria    # List of testable criteria
applicable_regulations # List of regulations
applicable_controls    # List of controls
risks                  # List of {description, level, mitigation}
evidence               # Citations from RAG
confidence             # 0.0 - 1.0
is_ambiguous           # Boolean
is_incomplete          # Boolean
is_conflicting         # Boolean
is_duplicate           # Boolean
quality_issues         # List of detected issues
status                 # raw → extracted → structured → analysed → validated → approved
version                # Integer, incremented on change
is_current             # Boolean
previous_version_id    # FK to prior version
source_conversation_id # Traceability link
source_document_id     # Traceability link
linked_artefacts       # List of artefact IDs
created_at, updated_at, approved_at, approved_by
```

## Status Lifecycle
```
RAW → EXTRACTED → NEEDS_CLARIFICATION → STRUCTURED → ANALYSED
    → VALIDATED → PENDING_APPROVAL → APPROVED
                                   → REJECTED
                                   → CONFLICTED
                                   → SUPERSEDED → CHANGED
```

## Versioning
- Every update creates an immutable `RequirementVersion` snapshot
- Historical versions are never destroyed
- `is_current` flag marks the active version
