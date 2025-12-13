## Summary

- In each subcomponent we need to add more traceability,accountability and evolvability. Add explicit links between artifacts (requirements, code, tests, PRs). Add owner of each component. Add some rules for changing files.

- In Changelog (Subcomponent) we need to link each change entry to the corresponding commits and pull requests.

## Traceability 

- Requirement ([US001](../requirements/user-stories.md)) -> Architecture ([Architecture](../architecture/architecture.md)) -> Code ([Code](../../app/src/services/reminder_service.py)) -> Test ([Test](../../app/tests/test_services/test_import_service.py)). This traces “create event” from story to design to implementation and verification.
- Quality requirement ([QAS002](../requirements/quality-requirements.md#qas002-reliable-reminder-scheduling)) -> Observability plan ([observability](../architecture/observability.md)) -> Telemetry setup ([telemetry](../../app/src/services/metrics_service.py)) -> Dashboard evidence ([Dashboard](https://cringineers.grafana.net/dashboard/snapshot/OhC5I5PhO1lIgcnU5PmRFNRTn6GZtt70)). This covers reliability of reminders from goal to monitoring evidence.
- Release note ([Changelog 0.1.0](../../CHANGELOG.md#010---2025-12-06)) -> Code changes ([Code](../../app/src/services/calendar_service.py)) -> Tests ([Test](../../app/tests/test_services/test_import_service.py)). Shows release item to implementation and validation.

## Review

All commits for accountability you can see [here](https://github.com/Inno-Cringineers/Telegram_Calendar/commits/main/)

### Product context

#### Vision and Scope
- **Evidence:** [description](../../README.md#description), [goals](../plan.md#project-goals).
- **Visibility:** **Strong** - Goals and scope are clearly stated in top-level documentation and referenced across project artifacts.
- **Accessibility:** **Strong** - Documentation is stored in the repository and accessible to all team members and stakeholders.
- **Accountability:** **Present** - Goals are listed, but no explicit owner is defined for each goal, but we can see who make commit.
- **Traceability:** **Present** - Features are mapped to user story IDs (e.g., US-001), but these are textual references rather than active links to requirement files or issues.
- **Evolvability:** **Present** - The plan can be updated, but lacks a version log or change history to track evolution.(only in commits)

#### Context and component diagrams
- **Evidence:** [context diagram](../architecture/architecture.md#context-diagram), [component diagram](../architecture/architecture.md#component-diagram).
- **Visibility:** **Strong** - Diagrams are prominently linked from the architecture documentation and repository index.
- **Accessibility:** **Strong** - PNG assets are stored in the repo.
- **Accountability:** **Present** - No explicit ownership is defined, but authors can be identified via Git commit history.
- **Traceability:** **Present** - Diagrams reference components by name, but do not include hyperlinks to corresponding code.
- **Evolvability:** **Present** - Editable PlantUML sources allow updates, but no version tags or baselines are maintained.

### Requirements

#### User stories
- **Evidence:** [User stories](../requirements/user-stories.md).
- **Visibility:** **Present** - A comprehensive table with detailed descriptions is available.
- **Accessibility:** **Strong** - File is stored in the repository.
- **Accountability:** **Present** - Stories are structured but lack explicit authorship, but we can see who make commit.
- **Traceability:** **Present** - IDs (US-001, etc.) are referenced across documents, but no direct links to code.
- **Evolvability:** **Present** - File easy editing, but no versioning or change log is kept.

#### Constraints
- **Evidence:** [Constraints](../requirements/constraints.md).
- **Visibility:** **Present** - A dedicated document clearly lists all project constraints.
- **Accessibility:** **Strong** - Concise table format, stored in the repository.
- **Accountability:** **Present** - Constraints are documented but not assigned to owners, but we can see who make commit.
- **Traceability:** **Present** - Referenced implicitly in architecture and planning documents; not explicitly linked to implementation decisions.
- **Evolvability:** **Present** - file can update, but no history of changes is tracked.

#### Quality requirements
- **Evidence:** [Quality requirements](../requirements/quality-requirements.md).
- **Visibility:** **Strong** - Quality attributes and scenarios are clearly documented.
- **Accessibility:** **Strong** - File is stored in the repository.
- **Accountability:** **Present** - Scenarios are defined but lack assigned owners, but we can see who make commit.
- **Traceability:** **Present** - QAS/QAST IDs are reused in testing documentation, but links to code and monitoring are not automated.
- **Evolvability:** **Present** - Editable format supports updates; no versioning or baseline process defined.

### Planning

#### Roadmap and milestones
- **Evidence:** [Plan](../plan.md).
- **Visibility:** **Strong** - Goals, roadmap, and MVP scope are clearly stated.
- **Accessibility:** **Strong** - Document is accessible in the repository.
- **Accountability:** **Present** - No ownership is assigned to milestones or roadmap items,but we can see who make commit.
- **Traceability:** **Present** - Features are mapped to user stories and MVP, but no active links to backlog issues or code exist.
- **Evolvability:** **Present** - The plan can be updated, but lacks version tags or a change log.

#### Sprint planning scripts
- **Evidence:** [Meeting script](../sprints/sprint-5/script.md) and prior scripts.
- **Visibility:** **Present** - Scripts exist per sprint but are not aggregated or summarized in a central view.
- **Accessibility:** **Present** - Stored in the repository.
- **Accountability:** **Strong** - Speakers and facilitators are listed in meeting files.
- **Traceability:** **Present** - Links to meeting transcripts and recordings are provided, but not to backlog items or tasks.
- **Evolvability:** **Present** - file can be edited, but lacks version tags or a change log.

### Tracking

#### Meetings and action points
- **Evidence:** [Meeting](../sprints/sprint-5/meeting-1.md).
- **Visibility:** **Present** - Notes are kept per sprint but not summarized across sprints.
- **Accessibility:** **Present** - Stored in the repository.
- **Accountability:** **Strong** - Action items include assigned owners.
- **Traceability:** **Present** - Actions are documented but not linked to issues or pull requests.
- **Evolvability:** **Absent** - Each meeting creates a new file; no process for updating or closing past actions is defined.


### Architecture

#### Architecture overview and diagrams
- **Evidence:** [Architecture](../architecture/architecture.md).
- **Visibility:** **Strong** - High-level overview and diagrams are clearly presented.
- **Accessibility:** **Strong** - Document includes both diagrams and source files in repo.
- **Accountability:** **Present** - No owner, but we can see who make commit.
- **Traceability:** **Present** - Components map to service names, but no explicit links to code directories or modules exist.
- **Evolvability:** **Present** - PlantUML sources allow changes, but no versioning is applied.

#### Tech stack and observability
- **Evidence:** [tech-stack](../architecture/tech-stack.md), [Observability](../architecture/observability.md), [Telemetry-data](../architecture/telemetry-data.md).
- **Visibility:** **Strong** - Technology choices and observability strategy are well documented.
- **Accessibility:** **Strong** - Documents are stored in the repository.
- **Accountability:** **Present** - Decisions are listed but not assigned to owners, but we can see who make commit.
- **Traceability:** **Strong** - Clear references to metrics, telemetry modules, and dashboards (e.g., Grafana) are provided.
- **Evolvability:** **Present** - Documents can be updated, but no change log are maintained.

### Risks

#### Risk log and SLOs
- **Evidence:** [Observability](../architecture/observability.md).
- **Visibility:** **Present** - Risks and SLOs are included within the observability document.
- **Accessibility:** **Strong** - Document is accessible in the repository.
- **Accountability:** **Present** - Risks and SLOs are listed but not assigned to owners,but we can see who make commit.
- **Traceability:** **Present** - SLOs are tied to specific metrics and dashboards, but not to code or deployment artifacts.
- **Evolvability:** **Present** - The list can be extended, but no regular review or update process is defined.

### Implementation (Code)

#### Source code
- **Evidence:** [app src](../../app/src/) modules (handlers, services, repositories).
- **Visibility:** **Strong** - Code is organized into clear modules and directories.
- **Accessibility:** **Strong** - All source code is stored in the repository.
- **Accountability:** **Present** - we have tasks with assign [example](https://github.com/orgs/Inno-Cringineers/projects/15/views/1?pane=issue&itemId=139511212&issue=Inno-Cringineers%7CTelegram_Calendar%7C26).
- **Traceability:** **Present** - File names align with features, but no explicit links to user stories or requirements exist.
- **Evolvability:** **Present** - all changes writing in [CHANGELOG](../../CHANGELOG.md).

#### Tests and automation
- **Evidence:** [Testing](../automation/testing.md) and [app tests](../../app/tests/).
- **Visibility:** **Present** - Tests exist and testing guidance is documented.
- **Accessibility:** **Present** - Test files and documentation are stored in the repository.
- **Accountability:** **Present** - Testing responsibilities are not explicitly assigned to owners,but we can se who make commit.
- **Traceability:** **Present** - Some quality requirements (e.g., QAST001-1) are mapped in testing documentation.
- **Evolvability:** **Present** - file can be changed but update processes are not defined.

### Communication

#### Meeting artifacts
- **Evidence:** [Meeting](../sprints/sprint-5/meeting-1.md), recording link, transcript link.
- **Visibility:** **Present** - Artifacts are stored per sprint, not summarized centrally.
- **Accessibility:** **Present** - Markdown files are in the repo, but recordings may be on external drives.
- **Accountability:** **Strong** - Speakers and note-takers are identified.
- **Traceability:** **Present** - Actions are noted but not linked to backlog items or PRs.
- **Evolvability:** **Absent** - Each meeting creates a new file; no process for updating or closing past actions is defined.

#### Retrospectives
- **Evidence:** [Retrospective](../sprints/sprint-5/retrospective.md) and prior retros.
- **Visibility:** **Present** - Retrospectives are documented per sprint.
- **Accessibility:** **Strong** - Markdown files are stored in the repository.
- **Accountability:** **Present** - Issues and actions are noted but not assigned to specific owners.
- **Traceability:** **Absent** - Improvement items are not linked to tasks, backlog items, or outcomes in subsequent sprints.
- **Evolvability:** **Present** - Retrospectives can be updated.

### Releases

#### Changelog
- **Evidence:** [Changelog](../../CHANGELOG.md).
- **Visibility:** **Strong** - Versioned entries clearly describe changes per release.
- **Accessibility:** **Strong** - File is stored in the repository root.
- **Accountability:** **Present** - Releases are dated, but no approver or release manager is identified.
- **Traceability:** **Absent** - Features and fixes are listed, but not linked to commits, tags, or pull requests.
- **Evolvability:** **Present** - The changelog can be extended.

