# ADR-0008: Workspace First and Project Memory

**Date:** 2026-08-05  
**Status:** accepted for v0.1 architecture, partial MVP implementation  
**Decision owners:** Victor + ChatGPT

## Context

The first implementation treated dialogue and resume assessment as separate flows:

- chat messages were stored in a conversation;
- an uploaded resume was analyzed on a separate page;
- returning to the chat created a new context that did not know the resume or its analysis.

This caused an obvious product failure: after a detailed resume analysis, the assistant answered that it knew nothing about the user.

The platform also needs to support future long-running themes such as career development, AI architecture, security, education, construction, and OSINT without mixing their contexts.

## Decision

MONGOOSE AI adopts a **Workspace First** architecture.

A workspace is the durable boundary for one user goal, project, case, or evolving line of thought. It owns the context used by all experts.

```text
Workspace / Project
├── conversations
├── messages
├── documents
├── extracted text
├── structured facts
├── analyses
├── reports
├── tasks
├── timeline
└── audit events
```

All analysis profiles read the same workspace context. Switching from Career Strategist to Project Coach or Jungian Reflection changes the analytical perspective, not the underlying memory.

Sessions may later be saved as named projects and resumed. A project may contain multiple conversations and documents while preserving one coherent line of development.

## MVP implementation

For `v0.1`, implement only Workspace Lite:

- one active workspace per browser session;
- one active conversation;
- uploaded document text available to later dialogue;
- analysis results associated with the same workspace;
- PDF reports generated from dialogue, documents, analysis, and metadata;
- no enterprise CRM, vector database, Redis, Celery, or multi-user collaboration.

## Future implementation

After `v0.1`:

- named projects;
- multiple conversations per project;
- durable user memory;
- structured knowledge objects;
- selective retrieval and RAG;
- memory editing and deletion;
- CRM/client association;
- channel adapters;
- role-based access and audit controls.

## Privacy decision

Real personal resumes and personal identifiers must not be committed to GitHub. Public demos use synthetic personas and fictional histories. Local personal data must be removable and should not be logged.

## Considered alternatives

### Separate memory per module

Rejected because resume, chat, reports, and expert profiles would continue to contradict one another and duplicate data.

### One global memory for everything

Rejected because unrelated goals and projects would contaminate each other and create privacy and retrieval problems.

### Full enterprise knowledge platform immediately

Rejected for `v0.1` because it would delay completion of the homework and create excessive infrastructure complexity.

## Consequences

### Positive

- documents and dialogue form one coherent context;
- expert profiles can produce different conclusions from the same evidence;
- a project can be paused and resumed;
- the architecture naturally supports RAG, CRM, reports, and additional channels;
- the product becomes an AI workspace rather than a collection of unrelated pages.

### Trade-offs

- workspace identity and lifecycle must be designed carefully;
- context size will eventually require summarization and retrieval;
- privacy controls and data deletion become mandatory;
- migrations will be needed when moving from Workspace Lite to durable projects.

## Validation criterion

After uploading and analyzing a resume, the user must be able to return to the same workspace and ask, “What do you know about me?” The assistant must answer from the uploaded document and stored workspace context rather than claiming it has no information.
