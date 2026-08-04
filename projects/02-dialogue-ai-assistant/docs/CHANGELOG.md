# Changelog

All notable changes to MONGOOSE AI PLATFORM are documented here.

The format follows the principles of Keep a Changelog. The project is currently preparing release `v0.1.0`.

## [Unreleased]

### Added

- Premium Web Shell with branded favicon, logo, navigation, animated controls, responsive layout, and premium Dialogue Center.
- GigaChat dialogue integration through a provider abstraction.
- Conversation persistence and API endpoints.
- Analysis Factory with selectable expert profiles:
  - Career Strategist;
  - Career Mentor;
  - Project Coach;
  - Jungian Reflection.
- Structured second-model analysis validated with Pydantic.
- Report Factory with ReportLab PDF rendering.
- Professional Assessment / Career Track Builder.
- Resume text extraction from PDF, DOCX, and TXT.
- Navigation between dialogue and document assessment.
- Unified Workspace architecture documentation.
- Mandatory development documentation standard.
- Project Journal and ADR practice.

### Changed

- Replaced WeasyPrint with ReportLab to remove GTK/Pango/Cairo system dependencies and improve Windows portability.
- Improved analysis profile selector contrast and added expandable profile explanations.
- Career analysis now normalizes flexible LLM output before Pydantic validation.
- MVP scope frozen around Dialogue Center, Professional Assessment, Report Factory, Workspace Lite, Demo Mode, documentation, and tests.

### Fixed

- Request tracing middleware failure before authentication initialization.
- GigaChat SSL configuration for the local Windows environment.
- UTF-8 display and PowerShell response diagnostics.
- Invisible options in the dark analysis selector.
- CareerTrackResult validation errors caused by object-shaped list items and missing disclaimers.

### Security

- Resume uploads are limited to PDF, DOCX, and TXT with a 5 MB size limit.
- Uploaded resume files are processed in memory in the MVP and are not persisted.
- Real personal data is prohibited in public repository demo materials.
- Synthetic personas are required for Demo Mode.

## [0.1.0] — Planned

Release goal: a polished, complete implementation of DZ 2236 PRO with premium dialogue, second-model analysis, branded downloadable PDF, Professional Assessment, Workspace Lite, and safe synthetic demo data.
