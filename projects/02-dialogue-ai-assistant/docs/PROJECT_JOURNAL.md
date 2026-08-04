# MONGOOSE AI Project Journal

This journal records every meaningful change to the project. New entries are appended in reverse chronological order.

---

## PJ-0001 — Mandatory development documentation standard

**Date:** 2026-08-05  
**Time:** 00:55 Europe/Riga  
**Status:** completed  
**Authors:** Victor + ChatGPT

### Topic

Introduction of a mandatory engineering journal, ADR practice, release changelog, task traceability, and documented commit rationale.

### Reason

The platform is evolving rapidly across UI, dialogue, analysis, reports, career assessment, security, and workspace concepts. Without immediate documentation, it would become difficult to understand why decisions were made, which ideas belong to the MVP, and what changed for users.

### Decision

Adopt `MONGOOSE AI Development Standard v1.0`:

- every change is documented when introduced;
- every architectural decision receives an ADR;
- every release updates the changelog;
- every implementation task links to its reason and resulting commit;
- ideas outside the frozen MVP scope go to the Roadmap;
- real personal data must never be committed to the public repository.

### Files added

- `docs/DEVELOPMENT_STANDARD.md`
- `docs/PROJECT_JOURNAL.md`
- `docs/CHANGELOG.md`
- `docs/adr/ADR-0008-workspace-first-and-project-memory.md`

### Impact

The project now has a mandatory traceability standard. Future changes must record date, time, reason, implementation, affected modules, and user or architectural impact.

### Related decisions

- ADR-0008 — Workspace First and project memory.

---

## Entry template

```markdown
## PJ-XXXX — Short title

**Date:** YYYY-MM-DD  
**Time:** HH:MM timezone  
**Status:** planned | in progress | completed | superseded  
**Authors:** ...

### Topic

...

### Reason

...

### Decision

...

### Files or modules changed

- ...

### Impact

...

### Related records

- ADR-XXXX
- TASK-XXXX
- commit SHA
```
