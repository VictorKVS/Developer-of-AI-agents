# MONGOOSE AI Development Standard

**Version:** 1.0  
**Status:** mandatory  
**Adopted:** 2026-08-05

## 1. Main rule

> Every change must be documented at the moment it is introduced.

No feature, fix, refactoring, dependency change, architecture decision, UI change, security measure, or scope adjustment is considered complete until its reason and impact are recorded.

## 2. Required documentation layers

### Project Journal
Records the development process in chronological order.

Every entry must contain:

- date and local time;
- entry identifier;
- topic;
- reason for the change;
- decision taken;
- changed files or modules;
- user-facing or architectural impact;
- status;
- authorship.

### Architecture Decision Records
Every important architectural decision receives a separate ADR.

Each ADR contains:

- context and problem;
- considered options;
- accepted decision;
- consequences and trade-offs;
- implementation status.

### Changelog
Contains only release-level changes grouped by version:

- Added;
- Changed;
- Fixed;
- Security;
- Deprecated;
- Removed.

### Tasks
Each implementation task must record:

- purpose;
- scope;
- acceptance criteria;
- related ADR and journal entry;
- status;
- resulting commit.

### Roadmap
Contains future plans only. Ideas that are outside the frozen MVP scope must be placed there rather than added immediately to the codebase.

## 3. Commit rule

Each commit message and related documentation must answer:

1. What was changed?
2. Why was it necessary?
3. How was it implemented?
4. What changed for the user, platform, security, or architecture?

Recommended format:

```text
feat(workspace): introduce shared document and dialogue context

Reason:
Resume analysis was not available in later dialogue.

Solution:
Added a workspace context shared by documents and conversations.

Impact:
AI can use uploaded documents in later messages and reports.
```

## 4. Scope discipline

For release `v0.1`, the scope is frozen around:

- Premium UI;
- Dialogue Center;
- Analysis Factory;
- Professional Assessment;
- Report Factory;
- Workspace Lite;
- Demo Mode;
- documentation and tests.

All other ideas go to the Roadmap until the release is complete.

## 5. Privacy rule

No real personal resume, phone number, email address, employer history, or other personal data may be committed to the public repository.

Demonstrations must use synthetic personas and fictional documents.

## 6. Completion rule

A task is complete only when:

- code works;
- checks/tests pass;
- user-facing behavior is verified;
- journal entry is added;
- ADR is added or updated when architecture changed;
- changelog is updated when release behavior changed.
