# MONGOOSE AI Project Journal

This journal records every meaningful change to the project. New entries are appended in reverse chronological order.

---

## PJ-0004 — Career analysis JSON recovery

**Date:** 2026-08-05  
**Time:** 14:12 Europe/Riga  
**Status:** completed  
**Authors:** Victor + ChatGPT

### Topic

Hardening of structured Career Track parsing for non-ideal LLM responses.

### Reason

The resume file was extracted correctly and the LLM request completed, but `/career/` returned `Expecting value: line 1 column 1 (char 0)`. The parser expected a perfectly clean JSON string and could not handle an empty response, explanatory text before JSON, Markdown fences, or malformed JSON.

### Decision

- reject an empty model response with a clear diagnostic message;
- locate and parse the JSON object between the first `{` and last `}`;
- preserve support for fenced JSON;
- log a safe preview and exact line/column for malformed JSON;
- perform one controlled repair request asking the same provider to return only valid JSON;
- continue validating the normalized payload with Pydantic.

### Files or modules changed

- `apps/web/career_services.py`
- `docs/PROJECT_JOURNAL.md`

### Impact

Career Track generation is more resilient to common LLM formatting deviations. The user receives an actionable error instead of a raw `json.JSONDecodeError`, and a single automatic recovery attempt is made before the operation fails.

### Related records

- Commit `48f92f0`.

---

## PJ-0003 — Unified Workspace session key repair

**Date:** 2026-08-05  
**Time:** 10:56 Europe/Riga  
**Status:** completed  
**Authors:** Victor + ChatGPT

### Topic

Repair of the session contract between Professional Assessment and Dialogue Center.

### Reason

The resume upload and career analysis completed successfully, and `/chat/` opened in the same browser session, but the dialogue model still asked which resume the user meant. The cause was a key mismatch: `/career/` stored a dictionary under `workspace_context`, while the dialogue API still searched for deprecated keys `workspace_resume_text` and `workspace_career_track`.

### Decision

Use one canonical session object:

- `workspace_context.resume_text`;
- `workspace_context.career_track`;
- `workspace_context.document_name`;
- `workspace_context.target_role_title`.

The dialogue prompt now explicitly states that the resume is already loaded and the model must not ask the user to upload it again or clarify which resume is meant.

### Files or modules changed

- `apps/conversations/views.py`
- `docs/PROJECT_JOURNAL.md`

### Impact

The sequence `upload resume → build track → continue in chat` now uses the same session keys end to end. The API response retains the `workspace_context_used` diagnostic flag for verification.

### Related records

- ADR-0008 — Workspace First and project memory.
- PJ-0002 — Resume-aware Workspace Lite dialogue.
- Commit `d497b00`.

---

## PJ-0002 — Resume-aware Workspace Lite dialogue

**Date:** 2026-08-05  
**Time:** 09:50 Europe/Riga  
**Status:** completed  
**Authors:** Victor + ChatGPT

### Topic

Connection of Professional Assessment with Dialogue Center inside one server-side session.

### Reason

After uploading and analysing a resume, the user returned to the chat and asked for an information-security position assessment. The dialogue model answered that it had no information because the resume and career analysis were isolated on `/career/` and were not included in the conversation prompt.

### Decision

Implement Workspace Lite memory without introducing new database models or migrations:

- preserve the extracted resume text in the Django server-side session;
- preserve the validated Career Track result in the same workspace context;
- inject this workspace context as a system message before the stored dialogue history;
- require the model to ground answers in the resume, validated analysis, and current messages;
- create a real session key before a new conversation is stored;
- limit stored resume context to 24,000 characters for the MVP.

### Files or modules changed

- `apps/web/views.py`
- `apps/conversations/views.py`
- `docs/PROJECT_JOURNAL.md`

### Impact

The sequence `upload resume → build assessment → return to dialogue → ask about the candidate` now uses one shared context. Different analysis profiles can subsequently examine the same resume and dialogue without uploading the document again during the active browser session.

### Limitations

- memory is scoped to the current Django session;
- clearing browser cookies or server sessions removes the workspace context;
- persistent multi-project memory remains planned for v0.2;
- only the first 24,000 characters of the extracted resume are added to dialogue context in this MVP.

### Related records

- ADR-0008 — Workspace First and project memory.
- Commits `e6946e5` and `2a962de`.

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
