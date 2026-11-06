# Technical Discovery Specification Package

> Discovery specification for portfolio-app-new, approved in section 9. Later edits outside the Approval and Configuration Decisions sections need re-approval.

## Application: portfolio-app-new

- **Project Name**: portfolio-app-new
- **Document Version**: `1.0.0`
- **Author**: gamug and dova

---

## 1. Executive Summary & Vision

- **Problem Statement**: A knowledge graph (GraphDB, Docker container, version 11.5) holds real data, and GraphDB exposes LLM tools (SPARQL query, full-text search and others) through its API. There is no way to turn an exploratory conversation with the graph into a structured report.
- **Vision**: A chat interface connected to the knowledge graph, decoupled from a report visualizer shown beside it. From the chat history, an agent builds an HTML report that tells a story with the data (plots, tables and narrative), which the analyst can regenerate and download. The visualizer is built on the OpenUI framework (this repository is a fork of `thesysdev/openui`).
- **Success Metrics**: Answer accuracy against the graph: at least 90% of the questions in a curated question set with known correct answers are answered correctly. The project owners (gamug and dova) prepare the question set.
- **Personas**:
  - **Business analyst / report author**: chats with the graph, selects the useful Q&As, generates, edits and downloads reports.
    - Goals: explore the graph in natural language and turn the findings into a report that tells a story with the data.
    - Pain points: building reports by hand is slow; graph queries need technical skills; reports lack a story.

### System context (as stated)

- The chat connects to the graph through a **connector** that this project must develop. GraphDB 11.5 has no endpoint that answers a question: its Talk to Your Graph API provides only tool calling. The connector therefore runs DeepSeek as the chat agent and calls GraphDB's LLM tool API (`/rest/llm/tool/{configType}/{configId}` and its `/{toolType}` calls), which was inspected read-only on the running instance (see `adr-007`).
- The tool source is a single setting: a Talk to Your Graph agent created in the Workbench (`ttyg`) or a static YAML configuration (`yaml`). Neither is configured yet, and whichever works first in the first spike is used.
- The report agent uses a small set of skills. Initially there are two: one converts business questions into plots, the other puts those plots in the format the visualizer can render. The skills are specified later in the SDD process (not in this discovery).
- Sessions, chat history and reports are persisted in a small SQLite database.

### Global rules

- There is a single local user: no login and no access control.
- Every destructive action asks for confirmation and applies to the active session only.
- The interface and the generated reports follow the language the analyst writes in.
- If the SQLite database cannot be read or written, the system shows an error and leaves the visible state unchanged.
- There are no hard performance targets. Streaming and progress feedback are required instead.
- Buttons with nothing to erase are disabled. "Generate Report" and "Download Report" stay enabled and show a guiding message when pressed without history or without a report.

---

## 2. Use Case Specifications

### Use Case `UC-001`: Chat with the Knowledge Graph

- **Primary Actor**: Business analyst
- **Secondary Actors**: GraphDB LLM tool API, DeepSeek, SQLite database
- **Brief Description**: The analyst asks questions in natural language and receives answers from the knowledge graph. Answers stream into the chat. Each successful question-answer pair is stored in the active session.
- **Preconditions**:
  - A session is active.
  - The GraphDB tool source (agent or YAML configuration) is configured, and DeepSeek is configured.
- **Triggers**:
  - The analyst submits a question in the chat.

#### Basic Flow (Happy Path)
1. The analyst submits a question.
2. The system sends the question to DeepSeek through the connector. DeepSeek calls the GraphDB tools as needed.
3. The system streams the answer into the chat as it arrives.
4. The system stores the question-answer pair in the active session, marked as relevant by default.

#### Exception Flow `UC-001-EX1`: GraphDB or DeepSeek unreachable or returns an error
1. At step 2 or 3 of the basic flow, if GraphDB or DeepSeek is unreachable or returns an error, or the tool loop does not finish, the system shows an error in the chat.
2. The system does not store the failed question.
3. The use case ends in a failed state without changing the stored history.

#### Postconditions
- **Success**: The session history contains the new question-answer pair, marked as relevant.
- **Failure**: The session history is unchanged.

#### Non-Functional Constraints
- **Performance**: No hard target. Answers stream so the analyst sees progress.
- **Security**: No user authentication (single local user). The connector authenticates to GraphDB with HTTP basic authentication using the application user from `.env` (`KG_USER`, `KG_PASSWORD`), as verified read-only on the running instance.

---

### Use Case `UC-002`: Manage Sessions

- **Primary Actor**: Business analyst
- **Secondary Actors**: SQLite database
- **Brief Description**: The analyst creates, renames, switches between and deletes sessions. Each session holds its own chat history and at most one current report.
- **Preconditions**:
  - The application is running.
- **Triggers**:
  - The analyst uses a session control (create, rename, select, delete).

#### Basic Flow (Happy Path)
1. The analyst creates a session, or selects an existing one from the session list.
2. The system makes it the active session and loads its chat history and current report, if any.

#### Alternate Flow `UC-002-ALT1`: Rename a session
1. At step 1, the analyst renames a session.
2. The system stores the new name.
3. The flow rejoins the basic flow at step 2.

#### Alternate Flow `UC-002-ALT2`: Delete a session
1. At step 1, the analyst deletes a session.
2. The system asks for confirmation.
3. If confirmed, the system deletes the session with its history and report.
4. If the deleted session was the active one, the system creates a new empty session and makes it active.

#### Exception Flow `UC-002-EX1`: Database error
1. At any step, if the database cannot be read or written, the system shows an error and leaves the visible state unchanged.

#### Postconditions
- **Success**: Exactly one session is active, and its history and report are shown.
- **Failure**: The visible state and stored data are unchanged.

---

### Use Case `UC-003`: Generate Report

- **Primary Actor**: Business analyst
- **Secondary Actors**: Report agent with its skills, SQLite database
- **Brief Description**: The analyst presses "Generate Report". The report agent runs its skills over the Q&As marked as relevant and builds a report that tells a story with the data. The report streams progressively into the report panel beside the chat.
- **Preconditions**:
  - A session is active.
  - The session has at least one question-answer pair marked as relevant.
- **Triggers**:
  - The analyst presses "Generate Report".

#### Basic Flow (Happy Path)
1. The analyst presses "Generate Report".
2. The system disables the chat and shows that generation is in progress.
3. The system passes the marked Q&As to the report agent.
4. The agent runs its skills (business question to plot, plot to renderable format) and the report streams progressively into the report panel.
5. The system stores the report as the session's current report, replacing any previous one.
6. The system re-enables the chat.

#### Alternate Flow `UC-003-ALT1`: Regenerate over an existing or edited report
1. At step 1, if the session already has a report, the system rebuilds it from the currently marked Q&As.
2. The flow rejoins the basic flow at step 2.

#### Alternate Flow `UC-003-ALT2`: Analyst cancels
1. At step 2 to 4, the analyst cancels the generation.
2. The system stops the generation and keeps the previous report, if any.
3. The system re-enables the chat.

#### Exception Flow `UC-003-EX1`: No chat history
1. At step 1, if the session has no history, the system does not generate and asks the analyst to start the data exploration first.

#### Exception Flow `UC-003-EX2`: No Q&A marked as relevant
1. At step 1, if the session has history but no Q&A is marked as relevant, the system does not generate and asks the analyst to mark at least one Q&A.

#### Exception Flow `UC-003-EX3`: Generation fails
1. At step 3 or 4, if the report agent fails, the system shows an error.
2. The partial report streamed so far becomes the session's current report, flagged as incomplete, and replaces the previous report.
3. The system re-enables the chat.

#### Postconditions
- **Success**: The session's current report is the newly generated one.
- **Cancel**: The previous report, if any, is unchanged.
- **Agent failure**: The current report is the partial report, flagged incomplete.

#### Non-Functional Constraints
- **Performance**: No hard target. The report streams progressively and the interface shows progress.

---

### Use Case `UC-004`: Edit Report Manually (Won't Have in the MVP, deferred for time)

> Deferred: there is not enough time to build manual editing in the MVP. The use case is kept for later iterations. `FR-020`, `FR-023`, `FR-024`, `FR-025` and `US-005` trace to it and are Won't Have.

- **Primary Actor**: Business analyst
- **Secondary Actors**: SQLite database
- **Brief Description**: The analyst changes the current report in the interface without using the chat: narrative text, and the order and presence of sections. Editing chart properties is out of scope for the MVP.
- **Preconditions**:
  - A session is active and has a current report.
- **Triggers**:
  - The analyst edits an element of the report in the report panel.

#### Basic Flow (Happy Path)
1. The analyst edits a narrative text block, or reorders or removes a section.
2. The system updates the report panel.
3. The system stores the edited report as the session's current report.

#### Exception Flow `UC-004-EX1`: No report
1. If the session has no report, no edit controls are available.

#### Exception Flow `UC-004-EX2`: Database error
1. At step 3, if the database cannot be written, the system shows an error and leaves the visible state unchanged.

#### Postconditions
- **Success**: The stored report contains the analyst's edits. A later regeneration would overwrite them.
- **Failure**: The visible and stored report are unchanged.

#### Notes
- No undo or redo in the first release.

---

### Use Case `UC-005`: Download Report

- **Primary Actor**: Business analyst
- **Secondary Actors**: None
- **Brief Description**: The analyst downloads the current report as a single self-contained HTML file that opens offline in a browser with charts, styles and data inlined.
- **Preconditions**:
  - A session is active and has a current report.
- **Triggers**:
  - The analyst presses "Download Report".

#### Basic Flow (Happy Path)
1. The analyst presses "Download Report".
2. The system builds one self-contained HTML file from the current report.
3. The browser downloads the file.

#### Exception Flow `UC-005-EX1`: No report built
1. At step 1, if the session has no report, the system does not download and tells the analyst that no report exists yet and asks to generate one first.

#### Postconditions
- **Success**: The analyst has the HTML file. The stored report is unchanged.
- **Failure**: No file is produced. The stored report is unchanged.

#### Notes
- The file is named `<session-name>-<YYYY-MM-DD>.html`, using the download date.

---

### Use Case `UC-006`: Erase History

- **Primary Actor**: Business analyst
- **Secondary Actors**: SQLite database
- **Brief Description**: The analyst erases the entire chat history of the active session. This also erases the session's report.
- **Preconditions**:
  - A session is active.
- **Triggers**:
  - The analyst presses "Erase History".

#### Basic Flow (Happy Path)
1. The analyst presses "Erase History".
2. The system asks for confirmation.
3. The system erases all question-answer pairs of the active session and its current report.

#### Alternate Flow `UC-006-ALT1`: Analyst declines
1. At step 2, if the analyst declines, the system changes nothing.

#### Exception Flow `UC-006-EX1`: History already empty
1. If the active session has no history, the "Erase History" button is disabled.

#### Postconditions
- **Success**: The active session has no history and no report. Other sessions are unchanged.
- **Failure or declined**: The session is unchanged.

---

### Use Case `UC-007`: Erase Report

- **Primary Actor**: Business analyst
- **Secondary Actors**: SQLite database
- **Brief Description**: The analyst erases the current report of the active session and keeps the chat history.
- **Preconditions**:
  - A session is active and has a current report.
- **Triggers**:
  - The analyst presses "Erase Report".

#### Basic Flow (Happy Path)
1. The analyst presses "Erase Report".
2. The system asks for confirmation.
3. The system erases the session's current report.

#### Alternate Flow `UC-007-ALT1`: Analyst declines
1. At step 2, if the analyst declines, the system changes nothing.

#### Exception Flow `UC-007-EX1`: No report
1. If the active session has no report, the "Erase Report" button is disabled.

#### Postconditions
- **Success**: The active session has no report and keeps its history. Other sessions are unchanged.
- **Failure or declined**: The session is unchanged.

---

### Use Case `UC-008`: Delete a Question-Answer Pair

- **Primary Actor**: Business analyst
- **Secondary Actors**: SQLite database
- **Brief Description**: The analyst deletes one specific question-answer pair from the active session's history. An existing report is not changed until it is regenerated.
- **Preconditions**:
  - A session is active and its history contains the pair.
- **Triggers**:
  - The analyst chooses to delete a question-answer pair.

#### Basic Flow (Happy Path)
1. The analyst chooses to delete a pair.
2. The system asks for confirmation.
3. The system deletes the pair from the active session.

#### Alternate Flow `UC-008-ALT1`: Analyst declines
1. At step 2, if the analyst declines, the system changes nothing.

#### Postconditions
- **Success**: The pair no longer exists in the session. The session's current report is unchanged.
- **Failure or declined**: The history is unchanged.

---

### Use Case `UC-009`: Mark Q&A Relevance

- **Primary Actor**: Business analyst
- **Secondary Actors**: SQLite database
- **Brief Description**: Each question-answer pair has a relevance toggle. Only pairs marked as relevant feed report generation (`UC-003`). New pairs are marked by default.
- **Preconditions**:
  - A session is active and its history contains the pair.
- **Triggers**:
  - The analyst switches the relevance toggle of a pair.

#### Basic Flow (Happy Path)
1. The analyst switches the toggle of a pair.
2. The system stores the new relevance state of the pair.
3. The system shows the updated state.

#### Exception Flow `UC-009-EX1`: Database error
1. At step 2, if the database cannot be written, the system shows an error and leaves the toggle unchanged.

#### Postconditions
- **Success**: The pair's relevance state is stored. The current report is unchanged.
- **Failure**: The relevance state is unchanged.

### Scope boundaries

- **In scope**: chat with the graph with streaming answers, session management (create, rename, switch, delete), relevance marking, report generation, HTML download, and the erase and delete actions above.
- **Out of scope for the MVP (stated)**: manual report editing (text, section order and removal; deferred for time); editing chart properties; asking the agent through the chat to tweak the existing report; report formats other than HTML (for example PDF); multiple users, sharing and authentication.

---

## 3. Functional Requirements & User Stories

> `FR-001` is reserved for SDD initialization. Priorities: UC-002, UC-008 and UC-009 were set to Must Have by the project owners; UC-001, UC-003, UC-005, UC-006 and UC-007 are core to the original brief and are Must Have; UC-004 (manual report editing) and its requirements are Won't Have for the MVP because of time. Each requirement takes the priority of the use case it traces to.

### Functional Requirements (EARS Syntax)

| Requirement ID | EARS Pattern | Statement | MoSCoW Priority | Traceability |
| :--- | :--- | :--- | :--- | :--- |
| `FR-002` | Event-Driven | WHEN the analyst submits a question, the system shall send it to DeepSeek through the connector, let DeepSeek query the knowledge graph through the GraphDB LLM tool API, and stream the answer into the chat as it arrives. | Must Have | `UC-001` |
| `FR-003` | Event-Driven | WHEN an answer completes, the system shall store the question text, the raw answer text and the OpenUI Lang version of the answer as a question-answer pair in the active session, marked as relevant. | Must Have | `UC-001`, `UC-009` |
| `FR-004` | Unwanted / Error | IF GraphDB or DeepSeek is unreachable, returns an error, or the tool loop does not finish, THEN the system shall show an error in the chat and shall not store the failed question. | Must Have | `UC-001` |
| `FR-005` | Ubiquitous | The system shall persist sessions, chat history, relevance marks and reports in a SQLite database so that they survive application restarts. | Must Have | `UC-001`, `UC-002`, `UC-003`, `UC-009` |
| `FR-006` | Event-Driven | WHEN the analyst creates a session, the system shall make it the active session with an empty history and no report. | Must Have | `UC-002` |
| `FR-007` | Event-Driven | WHEN the analyst selects a session, the system shall make it the active session and load its chat history and current report. | Must Have | `UC-002` |
| `FR-008` | Event-Driven | WHEN the analyst renames a session, the system shall store the new name. | Must Have | `UC-002` |
| `FR-009` | Event-Driven | WHEN the analyst confirms deleting a session, the system shall delete the session with its history and report. | Must Have | `UC-002` |
| `FR-010` | Unwanted / Error | IF the deleted session was the active session, THEN the system shall create a new empty session and make it the active session. | Must Have | `UC-002` |
| `FR-011` | Unwanted / Error | IF the database cannot be read or written, THEN the system shall show an error and leave the visible state unchanged. | Must Have | `UC-002`, `UC-004`, `UC-009` |
| `FR-012` | Event-Driven | WHEN the analyst switches the relevance toggle of a question-answer pair, the system shall store the new relevance state of the pair. | Must Have | `UC-009` |
| `FR-013` | Event-Driven | WHEN the analyst presses "Generate Report" and the active session has at least one pair marked as relevant, the system shall pass the marked pairs to the report agent and stream the report progressively into the report panel. | Must Have | `UC-003` |
| `FR-014` | Unwanted / Error | IF the analyst presses "Generate Report" and the active session has no history, THEN the system shall not generate and shall ask the analyst to start the data exploration first. | Must Have | `UC-003` |
| `FR-015` | Unwanted / Error | IF the analyst presses "Generate Report" and the active session has history but no pair marked as relevant, THEN the system shall not generate and shall ask the analyst to mark at least one pair. | Must Have | `UC-003` |
| `FR-016` | State-Driven | WHILE a report is being generated, the system shall disable the chat and show a progress indication. | Must Have | `UC-003` |
| `FR-017` | Event-Driven | WHEN the analyst cancels a report generation, the system shall stop it, keep the previous report if any, and re-enable the chat. | Must Have | `UC-003` |
| `FR-018` | Event-Driven | WHEN a report generation completes, the system shall store the report as the current report of the session, replacing any previous report. | Must Have | `UC-003` |
| `FR-019` | Unwanted / Error | IF the report agent fails during generation, THEN the system shall show an error, keep the partial report as the current report flagged as incomplete, and re-enable the chat. | Must Have | `UC-003` |
| `FR-020` | Event-Driven | WHEN the analyst regenerates a report that has manual edits, the system shall warn that regeneration overwrites the edits and continue only after confirmation. | Won't Have | `UC-003`, `UC-004` |
| `FR-021` | Ubiquitous | The system shall build each report from plots, tables of the returned data and narrative text that together tell a story with the data. | Must Have | `UC-003` |
| `FR-022` | Ubiquitous | The system shall show the chat panel and the report panel side by side. | Must Have | `UC-003` |
| `FR-023` | Event-Driven | WHEN the analyst edits a narrative text block of the current report, the system shall update the report panel and store the edited report. | Won't Have | `UC-004` |
| `FR-024` | Event-Driven | WHEN the analyst reorders or removes a section of the current report, the system shall update the report panel and store the edited report. | Won't Have | `UC-004` |
| `FR-025` | State-Driven | WHILE the active session has no report, the system shall not offer report editing controls. | Won't Have | `UC-004` |
| `FR-026` | Event-Driven | WHEN the analyst presses "Download Report" and the session has a report, the system shall download one self-contained HTML file named `<session-name>-<YYYY-MM-DD>.html`. | Must Have | `UC-005` |
| `FR-027` | Unwanted / Error | IF the analyst presses "Download Report" and the session has no report, THEN the system shall not download and shall tell the analyst to generate a report first. | Must Have | `UC-005` |
| `FR-028` | Event-Driven | WHEN the analyst confirms "Erase History", the system shall erase all question-answer pairs and the report of the active session. | Must Have | `UC-006` |
| `FR-029` | State-Driven | WHILE the active session has no history, the system shall disable "Erase History". | Must Have | `UC-006` |
| `FR-030` | Event-Driven | WHEN the analyst confirms "Erase Report", the system shall erase the report of the active session and keep its history. | Must Have | `UC-007` |
| `FR-031` | State-Driven | WHILE the active session has no report, the system shall disable "Erase Report". | Must Have | `UC-007` |
| `FR-032` | Event-Driven | WHEN the analyst confirms deleting a question-answer pair, the system shall delete the pair from the active session and leave the current report unchanged. | Must Have | `UC-008` |
| `FR-033` | Ubiquitous | The system shall ask for confirmation before deleting a session, a question-answer pair, a history or a report, and shall change nothing when the analyst declines. | Must Have | `UC-002`, `UC-006`, `UC-007`, `UC-008` |
| `FR-034` | Ubiquitous | The system shall apply every erase and delete action to the active session only. | Must Have | `UC-002`, `UC-006`, `UC-007`, `UC-008` |
| `FR-035` | Ubiquitous | The system shall write the interface text and the generated reports in the language the analyst writes in. | Must Have | `UC-001`, `UC-003` |

- **MVP Won't Have**: manual report editing (text, section order and removal; deferred for time); editing chart properties; asking the agent through the chat to tweak the existing report; report formats other than HTML (for example PDF); multiple users, sharing and authentication.

### Non-Functional Requirements (NFRs)

- **Performance**: No hard targets. Chat answers stream, and report generation streams progressively with a progress indication.
- **Reliability & Availability**: No availability target. Sessions, history, relevance marks and reports persist across application restarts.
- **Security**: The application runs locally for one user, with no login. Data leaves the machine only to the GraphDB agent endpoint and the LLM. Secrets such as API keys are kept in environment variables and are not committed.
- **Accuracy**: At least 90% of the questions in a curated question set with known correct answers, prepared by the project owners, are answered correctly.
- **Maintainability**: Code is checked by ruff, mypy, ESLint, Prettier and tsc, and tested with pytest and Vitest, all enforced in the pre-commit hook and CI. There is no minimum test coverage threshold for the MVP.

### User Story `US-001`: Chat with the knowledge graph

- **Card**: As a business analyst, I want to ask questions about the knowledge graph in natural language, so that I can explore the data without writing graph queries.
- **Epic**: Chat
- **Priority**: Must Have
- **Traceability**: `FR-002`, `FR-003`, `FR-004`, `FR-035`

#### Acceptance Criteria (Given-When-Then)
```gherkin
SCENARIO 1: Successful question
  GIVEN an active session
  WHEN the analyst submits a question
  THEN the answer streams into the chat
  AND the question-answer pair is stored in the session, marked as relevant

SCENARIO 2: Agent error
  GIVEN an active session
  WHEN the agent is unreachable or returns an error
  THEN the chat shows an error
  AND the failed question is not stored
```

### User Story `US-002`: Keep my work in sessions

- **Card**: As a business analyst, I want to create, rename, switch and delete sessions, so that I can keep separate explorations and return to them later.
- **Epic**: Sessions
- **Priority**: Must Have
- **Traceability**: `FR-005`, `FR-006`, `FR-007`, `FR-008`, `FR-009`, `FR-010`, `FR-011`

#### Acceptance Criteria (Given-When-Then)
```gherkin
SCENARIO 1: Switch session
  GIVEN two sessions with different histories
  WHEN the analyst selects the other session
  THEN its history and report are shown

SCENARIO 2: Delete the active session
  GIVEN an active session and the analyst confirms deleting it
  WHEN the deletion completes
  THEN the session, its history and its report no longer exist
  AND a new empty session is active

SCENARIO 3: Restart
  GIVEN sessions with history and reports
  WHEN the application restarts
  THEN the sessions, histories and reports are available

SCENARIO 4: Database error
  GIVEN a database that cannot be written
  WHEN the analyst renames a session
  THEN an error is shown
  AND the visible state is unchanged
```

### User Story `US-003`: Choose what goes into the report

- **Card**: As a business analyst, I want to mark which question-answer pairs are relevant, so that the report only contains the findings I care about.
- **Epic**: Chat history
- **Priority**: Must Have
- **Traceability**: `FR-003`, `FR-012`

#### Acceptance Criteria (Given-When-Then)
```gherkin
SCENARIO 1: Default state
  GIVEN a new question-answer pair
  WHEN it is stored
  THEN it is marked as relevant

SCENARIO 2: Unmark a pair
  GIVEN a pair marked as relevant
  WHEN the analyst switches its toggle
  THEN the pair is stored as not relevant
  AND the current report is unchanged
```

### User Story `US-004`: Generate a report from the exploration

- **Card**: As a business analyst, I want to press "Generate Report" and get a report that tells a story with my data, so that I don't build it by hand.
- **Epic**: Reporting
- **Priority**: Must Have
- **Traceability**: `FR-013`, `FR-014`, `FR-015`, `FR-016`, `FR-017`, `FR-018`, `FR-019`, `FR-021`, `FR-022`

#### Acceptance Criteria (Given-When-Then)
```gherkin
SCENARIO 1: Successful generation
  GIVEN a session with at least one pair marked as relevant
  WHEN the analyst presses "Generate Report"
  THEN the chat is disabled and progress is shown
  AND the report streams into the report panel beside the chat
  AND the report becomes the session's current report

SCENARIO 2: No history
  GIVEN a session with no history
  WHEN the analyst presses "Generate Report"
  THEN the system asks the analyst to start the data exploration
  AND no generation starts

SCENARIO 3: Nothing marked
  GIVEN a session with history and no pair marked as relevant
  WHEN the analyst presses "Generate Report"
  THEN the system asks the analyst to mark at least one pair

SCENARIO 4: Cancel
  GIVEN a generation in progress and a previous report
  WHEN the analyst cancels
  THEN the previous report is kept
  AND the chat is enabled

SCENARIO 5: Agent failure
  GIVEN a generation in progress
  WHEN the report agent fails
  THEN an error is shown
  AND the partial report is the current report, flagged incomplete

SCENARIO 6: Regenerate over an existing report
  GIVEN a session with a current report and at least one pair marked as relevant
  WHEN the analyst presses "Generate Report"
  THEN the report is rebuilt from the marked pairs
  AND replaces the previous report
```

### User Story `US-005`: Edit the report by hand

- **Card**: As a business analyst, I want to edit the narrative text and reorder or remove sections, so that I can polish the report before sharing it.
- **Epic**: Reporting
- **Priority**: Won't Have
- **Traceability**: `FR-011`, `FR-023`, `FR-024`, `FR-025`

#### Acceptance Criteria (Given-When-Then)
```gherkin
SCENARIO 1: Edit text
  GIVEN a current report
  WHEN the analyst edits a narrative text block
  THEN the report panel shows the edit
  AND the edit is stored

SCENARIO 2: Remove a section
  GIVEN a current report
  WHEN the analyst removes a section
  THEN the section disappears from the panel
  AND the stored report no longer contains it

SCENARIO 3: No report
  GIVEN a session with no report
  WHEN the analyst looks at the report panel
  THEN no editing controls are offered
```

### User Story `US-006`: Download the report

- **Card**: As a business analyst, I want to download the report as one HTML file, so that I can share it and open it offline.
- **Epic**: Reporting
- **Priority**: Must Have
- **Traceability**: `FR-026`, `FR-027`

#### Acceptance Criteria (Given-When-Then)
```gherkin
SCENARIO 1: Download
  GIVEN a session named "Q3 sales" with a report
  WHEN the analyst presses "Download Report" on 2026-11-05
  THEN one HTML file named "Q3 sales-2026-11-05.html" is downloaded
  AND it opens offline with its charts, styles and data

SCENARIO 2: No report
  GIVEN a session with no report
  WHEN the analyst presses "Download Report"
  THEN no file is downloaded
  AND the system tells the analyst to generate a report first
```

### User Story `US-007`: Erase history, report or a single answer

- **Card**: As a business analyst, I want to erase the history, the report or a single question-answer pair, so that I can start over or remove findings I no longer want.
- **Epic**: Chat history
- **Priority**: Must Have
- **Traceability**: `FR-028`, `FR-029`, `FR-030`, `FR-031`, `FR-032`, `FR-033`, `FR-034`

#### Acceptance Criteria (Given-When-Then)
```gherkin
SCENARIO 1: Erase history
  GIVEN a session with history and a report
  WHEN the analyst confirms "Erase History"
  THEN the history and the report of that session are erased
  AND other sessions are unchanged

SCENARIO 2: Erase report only
  GIVEN a session with history and a report
  WHEN the analyst confirms "Erase Report"
  THEN the report is erased
  AND the history is kept

SCENARIO 3: Delete one pair
  GIVEN a session with a report and several pairs
  WHEN the analyst confirms deleting one pair
  THEN only that pair is removed
  AND the report is unchanged

SCENARIO 4: Declined confirmation
  GIVEN any erase or delete action
  WHEN the analyst declines the confirmation
  THEN nothing changes

SCENARIO 5: Nothing to erase
  GIVEN a session with no history and no report
  WHEN the analyst looks at the buttons
  THEN "Erase History" and "Erase Report" are disabled
```

---

## 4. Technology Stack Selection & MCDM Matrix

### Constraints that shape the choice

- **Timeline**: the MVP must be built in 1 week.
- **Team**: gamug and dova know Python (FastAPI or similar), SPARQL and GraphDB, and Node.js backends. gamug is related to Node.js but not an expert, and the team accepts Node.js tooling for the frontend.
- **LLM**: DeepSeek, called with an API key stored in a `.env` file. GraphDB's Talk to Your Graph is also configured with DeepSeek, according to the project owners.
- **Fixed inputs**: GraphDB 11.5 in Docker (inspected: 11.5.1, free edition) with its LLM tool API; the OpenUI framework as the visualizer base (this repository is a fork of `thesysdev/openui`); SQLite for sessions, history and reports.
- **Weights (set by the project owners)**: Speed to MVP and Team skill alignment 5; OpenUI compatibility 4; all other criteria 3.

### Decisions made by the project owners (no matrix)

| Category | Decision | Reason given |
| :--- | :--- | :--- |
| Backend | Python with FastAPI | Team strength in Python; the repository has a FastAPI example (`examples/app-frameworks/fastapi`) that streams NDJSON to a React client. |
| LLM | DeepSeek, API key in `.env` | Same provider as GraphDB's Talk to Your Graph configuration; the key stays in an environment variable and is not committed. |
| Persistence | SQLite | Requested for sessions, history and reports. |

### Multi-Criteria Decision-Making (MCDM) Evaluation

> The scores below are a proposal for the project owners to review. They are judgements, not measurements. Scores are 1 to 5.

#### Category: Frontend host for the chat and report panels

| Evaluation Criteria | Weight (1-5) | Option A: Vite + React SPA | Option B: Next.js |
| :--- | :---: | :---: | :---: |
| **Speed to MVP** | 5 | 5 | 3 |
| **Team Skill Alignment** | 5 | 4 | 3 |
| **OpenUI Compatibility** | 4 | 5 | 4 |
| **Maintainability** | 3 | 4 | 3 |
| **AI Ecological Adaptability** | 3 | 3 | 3 |
| **LLM AI Coding Proficiency** | 3 | 4 | 4 |
| **Weighted Score Total** | -- | **98** | **76** |

Scoring notes:

- **Speed to MVP**: the repository's FastAPI example is already a Vite + React app with the OpenUI chat interface and a streaming adapter. With Next.js the server routes are redundant because FastAPI serves the API, so the example would need adapting.
- **Team Skill Alignment**: a single-page app needs less Node.js server knowledge than Next.js, and gamug is not a Node.js expert.
- **OpenUI Compatibility**: both are supported (the CLI templates use Next.js). The FastAPI example is the closest reference to the chosen backend.
- **AI Ecological Adaptability**: equal, because the frontend does not call ML frameworks.

**Decision**: Option A, Vite + React single-page app, with a FastAPI backend.

#### Selected Stack

- **Frontend**: Vite + React with the OpenUI packages (`@openuidev/react-lang`, `@openuidev/react-ui`, `@openuidev/react-headless`), for the chat and the report panel.
- **Backend**: Python with FastAPI. It hosts the connector to GraphDB's LLM tools, the sessions API over SQLite and the report agent.
- **Data storage**: SQLite for sessions, chat history, relevance marks and reports.
- **LLM**: DeepSeek, with the API key in `.env`.
- **DevOps / hosting**: local single-user run, with GraphDB 11.5 in a Docker container. The application is started in the devcontainer with two commands: `uvicorn` for the FastAPI backend and the Vite dev server for the frontend, which proxies `/api` to the backend.

Open technical choices carried to Phase 4 (ADRs): how the report agent is orchestrated, how the report is rendered with OpenUI and inlined into one HTML file, and how sessions map to the OpenUI thread storage.

---

## 5. Architecture Decision Records (ADRs)

### `adr-001`: Use Python with FastAPI for the backend

- **Context**: The application needs a backend for the connector to GraphDB's LLM tools, a sessions API over SQLite and the report agent. The MVP must be built in 1 week by a team that knows Python (FastAPI or similar), SPARQL and GraphDB, and Node.js backends. The repository already contains a FastAPI example (`examples/app-frameworks/fastapi`) that streams NDJSON to a React client.
- **Decision Drivers**:
  - **Business goal**: deliver the MVP in 1 week.
  - **Technical constraint**: the OpenUI frontend is React; the backend must stream responses and call an OpenAI-compatible LLM API (DeepSeek).
  - **Quality attribute**: team skill alignment and low setup cost.
- **Considered Options**:
  1. Python with FastAPI
  2. Node.js / TypeScript (Express or similar)
- **Decision**: Use Python with FastAPI. It matches the team's strongest skill, and the repository's FastAPI example is a working reference for the streaming endpoint and the React client.
- **Consequences (Positive)**: Fast start from an existing reference; the team works in its strongest language for the agent code.
- **Consequences (Trade-offs)**: The project uses two languages (Python backend, TypeScript frontend). The FastAPI example uses the hosted OpenUI Cloud, so its prompt and model wiring must be adapted to DeepSeek.
- **Mitigation**: Keep the API contract between frontend and backend small and documented; replace the example's Cloud-specific prompt with a locally generated system prompt (see `adr-006`).
- **Rejected Options**: Node.js / TypeScript: one language end to end and closer to the OpenUI server helpers, but gamug is not a Node.js expert and the team's agent experience is in Python.
- **Traceability**: `FR-002`, `FR-005`, `FR-013`
- **External Docs**: `examples/app-frameworks/fastapi/README.md`

### `adr-002`: Use a Vite + React single-page app as the frontend host

- **Context**: The chat and the report panel need a React host for the OpenUI packages. The backend is FastAPI (`adr-001`), so server routes in the frontend host would be redundant. The MCDM evaluation in section 4 scored the options with the project owners' weights.
- **Decision Drivers**:
  - **Business goal**: speed to MVP and team skill alignment (weight 5).
  - **Technical constraint**: OpenUI compatibility (weight 4); the host must run the OpenUI React packages.
  - **Quality attribute**: maintainability.
- **Considered Options**:
  1. Vite + React single-page app (score 98)
  2. Next.js (score 76)
- **Decision**: Use a Vite + React single-page app, with the Vite dev server proxying `/api/*` to FastAPI as the repository's FastAPI example does.
- **Consequences (Positive)**: Closest to the existing example; no server-side rendering concepts to learn.
- **Consequences (Trade-offs)**: No server-side rendering or Next.js route handlers; production serving of the built assets must be arranged separately.
- **Mitigation**: The application is a single-user local tool, so server-side rendering is not needed; static serving is decided in Phase 5.
- **Rejected Options**: Next.js: used by the CLI templates and fully supported, but its server routes duplicate FastAPI and the example would need adapting.
- **Traceability**: `FR-016`, `FR-022`
- **External Docs**: `docs/PRODUCT.md` section 4; `examples/app-frameworks/fastapi/frontend`

### `adr-003`: Use the react-ui chat layouts for the chat panel

- **Context**: The chat needs a message list, streaming display and a thread (session) list next to a report panel. Each question-answer pair also needs a relevance toggle and a delete action (`FR-012`, `FR-032`). The prebuilt chat layouts in `@openuidev/react-ui` (`OpenUIChat`, `AgentInterface`) are the fastest route, but it is not yet verified that they allow per-message controls.
- **Decision Drivers**:
  - **Business goal**: speed to MVP.
  - **Technical constraint**: the project owners chose to render the chat with OpenUI.
  - **Quality attribute**: consistency with the OpenUI look and streaming behaviour.
- **Considered Options**:
  1. react-ui chat layouts (`OpenUIChat` / `AgentInterface`)
  2. react-headless with a custom UI
- **Decision**: Use the react-ui chat layouts for the chat panel and place the report panel beside them.
- **Consequences (Positive)**: Streaming display, message rendering and the thread list come prebuilt.
- **Consequences (Trade-offs)**: Per-message relevance toggles and single-message delete may not be supported by the layout, which would force custom code or a switch of approach.
- **Mitigation**: Verify in the first spike that the layout can host the toggle and the delete action. If it cannot, fall back to `@openuidev/react-headless` with a custom UI and record a new ADR that supersedes this one.
- **Rejected Options**: react-headless with a custom UI: full control over the per-pair controls, but more components to build in a 1-week MVP.
- **Traceability**: `FR-007`, `FR-012`, `FR-022`, `FR-032`
- **External Docs**: `packages/react-ui/src/components/OpenUIChat`; `packages/react-ui/src/components/AgentInterface/README.md`

### `adr-004`: Persist sessions, history and reports in SQLite

- **Context**: Sessions, chat history, relevance marks and reports must survive application restarts for a single local user, and the analyst can switch between sessions. The project owners asked for a small SQLite database.
- **Decision Drivers**:
  - **Business goal**: keep the analyst's work between runs.
  - **Technical constraint**: single local user, no hosted database.
  - **Quality attribute**: persistence across restarts, simple setup.
- **Considered Options**:
  1. SQLite
  2. A hosted database such as Supabase (as in the repository's Supabase example)
- **Decision**: Use SQLite as the only store for sessions, question-answer pairs (question text, raw answer text and OpenUI Lang), relevance marks and one current report per session.
- **Consequences (Positive)**: No separate service to run; the database is a local file; fits the single-user scope.
- **Consequences (Trade-offs)**: Writes from concurrent requests need care; the file is local to one machine.
- **Mitigation**: A single local user keeps concurrency low; the schema is defined in the SDD design phase. Data errors are shown to the analyst without changing the visible state (`FR-011`).
- **Rejected Options**: Hosted database: provides auth, real-time updates and multi-device access, none of which are in scope.
- **Traceability**: `FR-005`, `FR-011`
- **External Docs**: `examples/miscellaneous/supabase/README.md` (alternative, not chosen)

### `adr-005`: Implement the OpenUI thread REST convention for sessions

- **Context**: Sessions need create, list, switch, rename and delete (`FR-006` to `FR-010`). The `@openuidev/react-headless` package provides `restStorage`, which expects list, create, get, update and delete endpoints under one base URL. The backend is FastAPI (`adr-001`) and the store is SQLite (`adr-004`).
- **Decision Drivers**:
  - **Business goal**: speed to MVP.
  - **Technical constraint**: the react-ui chat layout (`adr-003`) works with OpenUI storage adapters.
  - **Quality attribute**: little custom frontend code.
- **Considered Options**:
  1. FastAPI implements the OpenUI thread REST convention (`GET /get`, `POST /create`, `GET /get/{id}`, `PATCH /update/{id}`, `DELETE /delete/{id}`)
  2. Custom sessions API with a custom storage adapter
- **Decision**: Implement the thread REST convention in FastAPI over SQLite, so the frontend uses `restStorage` unchanged.
- **Consequences (Positive)**: The session list, rename and delete work with the existing OpenUI storage code.
- **Consequences (Trade-offs)**: Reports, relevance marks and the per-session report state are not part of the thread convention and need extra endpoints.
- **Mitigation**: Add separate report and relevance endpoints beside the thread endpoints, defined in the design phase.
- **Rejected Options**: Custom sessions API with a custom adapter: shaped exactly to this project, but more frontend code to write.
- **Traceability**: `FR-006`, `FR-007`, `FR-008`, `FR-009`, `FR-010`
- **External Docs**: `packages/react-headless/src/adapters/restStorage.ts`

### `adr-006`: Use DeepSeek as the only LLM, configured by environment variables, with a locally generated OpenUI prompt

- **Context**: GraphDB's Talk to Your Graph is configured with DeepSeek, according to the project owners. They want the same provider for the report agent and the OpenUI conversion, with the API key in a `.env` file. Data may leave the machine only to GraphDB and the LLM. The repository's FastAPI example uses the hosted OpenUI Cloud; the CLI also generates a system prompt locally from a component library.
- **Decision Drivers**:
  - **Business goal**: one provider and one key to manage.
  - **Technical constraint**: secrets must not be committed; no data may go to other services.
  - **Quality attribute**: DeepSeek must follow OpenUI Lang reliably, which is not verified yet.
- **Considered Options**:
  1. DeepSeek through an OpenAI-compatible client, with a locally generated OpenUI system prompt
  2. OpenUI Cloud / Gateway (hosted by Thesys)
- **Decision**: Call DeepSeek only, with the API key read from environment variables loaded from `.env`, and generate the OpenUI system prompt locally from the component library with the OpenUI CLI (self-hosted path).
- **Consequences (Positive)**: No third service holds the data; the key stays in `.env`; consistent with the security requirement.
- **Consequences (Trade-offs)**: DeepSeek's reliability in producing valid OpenUI Lang is unverified; the example's Cloud-specific prompt and model wiring must be replaced.
- **Mitigation**: Test conversion output against the library early; if invalid output is frequent, handle it through the parser's error reporting and a retry, and record the result as a risk. The model is `deepseek-chat` and the API base URL is `https://api.deepseek.com`, set in `.env` as `LLM_MODEL` and `LLM_URL`, with the key in `LLM_API_KEY`.
- **Rejected Options**: OpenUI Cloud / Gateway: works out of the box in the example and offers repair tooling, but sends data to a service outside the allowed list and does not use the project's DeepSeek key.
- **Traceability**: `FR-002`, `FR-013`
- **External Docs**: `packages/openui-cli/README.md`; `examples/app-frameworks/fastapi/backend/app/main.py`

### `adr-007`: Connect the chat to the knowledge graph through a FastAPI connector that runs a DeepSeek tool loop over GraphDB's LLM tool API

- **Context**: The analyst chats with the knowledge graph in natural language. Inspection of the running GraphDB 11.5.1 (read-only) and the official 11.5 documentation show that GraphDB does not expose an endpoint that takes a question and returns an answer. Its Talk to Your Graph API provides only tool calling: `POST /rest/ttyg/agents/{agentId}/{toolType}`, and the LLM integration API `GET /rest/llm/tool/{configType}/{configId}` (returns an OpenAPI description of the tools) with `POST /rest/llm/tool/{configType}/{configId}/{toolType}` (runs a tool). The tool types are `sparql_query`, `fts_search`, `similarity_search`, `retrieval_search`, `autocomplete_iri_discovery_search` and `iri_discovery_search`. `configType` is `ttyg` (tools of an agent created in the Workbench) or `yaml` (tools from a static YAML configuration). On the inspected instance no agent and no YAML configuration exists yet. The app user authenticates with HTTP basic authentication. The chat renders answers with OpenUI, and the project owners want both the raw answer and its OpenUI Lang stored.
- **Decision Drivers**:
  - **Business goal**: let the analyst question the graph without writing queries.
  - **Technical constraint**: the only programmatic interface is the tool API; credentials and keys must stay on the server; GraphDB may be reached only from the backend.
  - **Quality attribute**: the chat streams the answer, and answers are accurate against the graph (90% on the curated question set).
- **Considered Options**:
  1. FastAPI connector that runs DeepSeek as the chat agent with a tool loop over GraphDB's `/rest/llm/tool` API, then converts the final answer to OpenUI Lang with a second DeepSeek call
  2. The same tool loop, but the agent writes OpenUI Lang directly in one model loop
  3. FastAPI connector as an MCP client of GraphDB's `/mcp` server
  4. Call an answering Talk to Your Graph agent and convert its answer
- **Decision**: Build a FastAPI connector that runs DeepSeek as the chat agent. The connector reads the tool descriptions from `GET /rest/llm/tool/{configType}/{configId}`, gives them to DeepSeek as function definitions, forwards each tool call to `POST /rest/llm/tool/{configType}/{configId}/{toolType}` with the app user's credentials, and returns the results to DeepSeek until it produces a final answer. A second DeepSeek call converts the final answer to OpenUI Lang. The connector streams the result to the chat and stores the question, the raw answer and the OpenUI Lang only after the answer completes. The tool source is a single setting (`configType` of `ttyg` or `yaml`, plus `configId`), and whichever source works first in the first spike is used. The OpenUI conversion stays a second call.
- **Consequences (Positive)**: A documented, programmatic interface that needs no Workbench chat; the full flow runs in the backend where the keys stay; the tool descriptions come from GraphDB, so they follow the configured tools.
- **Consequences (Trade-offs)**: The backend owns the tool loop (prompting, iteration limit, error handling); each question costs several model calls and more latency, plus one for the conversion; DeepSeek's reliability with function calling and with GraphDB's tool schemas is unverified; conversion could alter the meaning of an answer.
- **Mitigation**: Limit tool-loop iterations and report a clear error when it is exceeded (`FR-004`); stream the final output; verify tool calling and conversion fidelity against the curated question set early in the first spike; keep the tool source behind one configuration setting.
- **Rejected Options**: Calling an answering agent: GraphDB's API provides only tool calling, so there is no such endpoint. MCP client of `/mcp`: documented for MCP clients, but it adds a protocol client and security settings on top of the REST tool API the project owners chose. Single-loop OpenUI answers (option 2): fewer calls, but the project owners chose to keep the conversion as a second call.
- **Traceability**: `FR-002`, `FR-003`, `FR-004`
- **External Docs**: `https://graphdb.ontotext.com/documentation/11.5/using-graphdb-llm-tools-with-external-clients.html`; `docs/PRODUCT.md` `RSK-001`

### `adr-008`: Orchestrate the report agent as sequential DeepSeek calls, one per skill

- **Context**: Report generation runs two skills: one converts business questions into plots, and one puts the plots in the format the visualizer renders. The skills themselves are specified later in the SDD process. The MVP has 1 week.
- **Decision Drivers**:
  - **Business goal**: deliver the MVP in 1 week.
  - **Technical constraint**: DeepSeek via an OpenAI-compatible API; the skill specifications are not written yet.
  - **Quality attribute**: cancel and progress support during generation (`FR-016`, `FR-017`).
- **Considered Options**:
  1. Sequential DeepSeek calls from FastAPI, one per skill
  2. LangGraph (Python) graph with a node per skill
- **Decision**: Run the two skills as sequential DeepSeek calls from FastAPI with an OpenAI-compatible client, with no agent framework.
- **Consequences (Positive)**: Smallest setup, easiest to cancel and stream, and nothing to learn before the skills are specified.
- **Consequences (Trade-offs)**: No built-in state, retries or routing; adding more skills later may require refactoring.
- **Mitigation**: Keep each skill behind one function with a defined input and output, so a framework can be introduced later through a new ADR.
- **Rejected Options**: LangGraph: gives structure for more skills, but needs more setup than the 1-week MVP allows for two steps.
- **Traceability**: `FR-013`, `FR-016`, `FR-017`, `FR-018`, `FR-019`
- **External Docs**: `templates/openui-self-hosted` (LangGraph base, not chosen)

### `adr-009`: Store the report as OpenUI Lang, render it in the report panel and export it by inlining the OpenUI browser bundle

- **Context**: The report must stream into a panel beside the chat, be stored per session, and be downloadable as one self-contained HTML file that opens offline (`FR-026`). The project owners chose to render the report with OpenUI and inline the result into one HTML file. `@openuidev/browser-bundle` ships the renderer, UI library, React and styles as one script and one stylesheet, and exposes `window.__OpenUI`.
- **Decision Drivers**:
  - **Business goal**: a shareable report that works offline.
  - **Technical constraint**: no external resources (no CDN) in the downloaded file.
  - **Quality attribute**: the downloaded report looks the same as the panel.
- **Considered Options**:
  1. Store OpenUI Lang; export HTML with the OpenUI Lang and the browser bundle inlined
  2. Have the agent write standalone HTML/CSS/JS with an inlined chart library
- **Decision**: The report agent produces OpenUI Lang, stored in SQLite as the session's report. The panel renders it with the `Renderer`. The download inlines the browser bundle's script and stylesheet and the stored OpenUI Lang into one HTML file named `<session-name>-<YYYY-MM-DD>.html`.
- **Consequences (Positive)**: One rendering path for the panel and the download; the report stays editable as text later.
- **Consequences (Trade-offs)**: Inlining the bundle makes each file large (the bundle's size is documented in its README); the inlining approach has not been tested.
- **Mitigation**: Verify inlining and offline opening in the first spike, and record the file size.
- **Rejected Options**: Standalone HTML written by the agent: portable, but the panel and the download would use two rendering paths and the agent would produce unvalidated HTML.
- **Traceability**: `FR-013`, `FR-018`, `FR-021`, `FR-022`, `FR-026`
- **External Docs**: `packages/browser-bundle/README.md`

---

## 6. Development Environment Setup

- **Target platforms**: Linux, through a VS Code devcontainer. Development is done inside the container on any host.
- **Source hosting**: GitHub fork `gamug/portfolio-app-new` (remote `fork`; upstream is `thesysdev/openui`). Access is over HTTPS with the `gh` CLI.
- **Runtimes and version managers**: `uv` for Python and `fnm` or `nvm` for Node.js. Versions are pinned in `.python-version` and `.nvmrc`: Python 3.12 and Node.js 22 (the root `package.json` requires Node.js `^20.19.0 || >=22.12.0`, so the pin must be 22.12 or newer). `.nvmrc` pins Node.js 22.12.
- **Environment isolation**: Devcontainer for the application (FastAPI backend and Vite frontend). GraphDB is not part of the devcontainer.
- **Local services**: GraphDB 11.5 is already running outside the project, and the project only needs its URL. GraphDB runs on the host machine, and the devcontainer reaches it at `http://host.docker.internal:7200` (`KG_HOST` in `.env`).
- **Editor configuration**: VS Code with shared workspace settings and recommended extensions committed: Dev Containers, Python, Ruff and Claude Code. The devcontainer installs `uv` and Node.js and the project's dependencies. ESLint and Prettier extensions were not selected.
- **Configuration variables**: `.env.example` is committed and lists `LLM_API_KEY`, `LLM_MODEL`, `LLM_URL`, `KG_HOST`, `KG_REPOSITORY`, `KG_USER`, `KG_PASSWORD` and `SQLITE_PATH`. All except `SQLITE_PATH` match the existing local, gitignored `.env` (`LLM_MODEL=deepseek-chat`, `LLM_URL=https://api.deepseek.com`, `KG_HOST=http://host.docker.internal:7200`, `KG_REPOSITORY=portfolio`). `KG_USER` must be a read-only GraphDB user (see `RSK-007`), and the admin credentials in `.env` (`KG_ADMIN_*`) are not used by the application. The tool configuration type and ID are added once the tool source is decided. Local values live in `.env`, which stays out of Git.
- **Code quality**: Python: `ruff` (lint and format) and `mypy`. Frontend: ESLint, Prettier and `tsc`. All run through the pre-commit hook and CI. Tests: `pytest` for the backend and Vitest for the frontend.
- **Verification command**: `uv run pytest` for the backend, the Vitest suite for the frontend, then a check of the backend health endpoint `GET /api/health`. The frontend uses `pnpm`, so its test command is `pnpm test`.

---

## 7. Risk Assessment & MVP Roadmap

### Risk Matrix

Impact and Probability use 1 (Low) to 3 (High); Score = Impact × Probability. A score of 6 or more requires a mitigation plan.

| Risk ID | Description | Impact | Probability | Score | Mitigation Plan |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `RSK-001` | GraphDB 11.5 has no endpoint that answers a question, so the chat depends on DeepSeek's tool calling over GraphDB's LLM tool API, and no tool source (agent or YAML configuration) is configured yet. If DeepSeek calls the tools unreliably, answer accuracy and the 90% metric suffer. | High (3) | Medium (2) | **6** | In the day 1-2 spike, test the tool loop on the live instance against the curated question set; limit the number of tool-loop iterations; enable only the tools the questions need; tune the system prompt. |
| `RSK-002` | DeepSeek produces invalid OpenUI Lang for the chat conversion or the report, so parts of the UI do not render. | High (3) | Medium (2) | **6** | In the spike, test generation against the component library with the locally generated prompt; use the parser's error reporting to detect broken statements and retry; record the failure rate. |
| `RSK-003` | The react-ui chat layout cannot host a relevance toggle and a delete action on each question-answer pair (`adr-003`). | Medium (2) | Medium (2) | **4** | Check in the spike. If it cannot, fall back to `@openuidev/react-headless` with a custom UI through a new ADR. |
| `RSK-004` | Inlining the OpenUI browser bundle produces a very large or non-working offline HTML file (`adr-009`). | Medium (2) | Medium (2) | **4** | Test inlining and offline opening in the spike and record the file size. |
| `RSK-005` | The 1-week schedule is too short for the Must Have scope. | High (3) | High (3) | **9** | Run the spike first on days 1-2 to remove the biggest unknowns; build Must Haves on days 3-5; check progress against the roadmap at the end of each day. The scope is not reduced without a decision from the project owners. |
| `RSK-006` | Reports are built from stored answer text only (`FR-003`), so plots may be weak or wrong when the answer text lacks the underlying figures. | High (3) | Medium (2) | **6** | Evaluate plot quality in the spike. If it is weak, propose a new ADR to also store the structured tool results; a schema change needs the project owners' approval. |
| `RSK-007` | The application user in `.env` has write rights on the `portfolio` repository, so SPARQL issued by the model could change graph data if the `sparql_query` tool permits updates. | High (3) | Medium (2) | **6** | Create a read-only GraphDB user for the application and set `KG_USER` and `KG_PASSWORD` to it; the application never uses a write-enabled or admin user. |

### Phased Roadmap

- **MVP**: All Must Have requirements in section 3: chat with the graph, session management, relevance marking, report generation (streamed, cancellable), HTML download, erase and delete actions, and the interface language rule. The MVP is built in 1 week.
- **Phase 0, Spike (days 1-2)**: Test the tool loop on the live GraphDB, DeepSeek tool calling and OpenUI Lang generation, whether the react-ui chat can host the per-pair controls, inlining of the browser bundle, and report plot quality. Create the read-only GraphDB user. Decide the tool source.
- **Phase 1, MVP build (days 3-5)**: Build the Must Have requirements on the chosen stack.
- **Phase 2, Testing and fixes (days 6-7)**: Test against the curated question set (90% target), fix defects and verify the environment.
- **Next phases (not in the MVP)**: Manual report editing (`UC-004`, `FR-020`, `FR-023` to `FR-025`), chart property editing, report tweaks through the chat, formats other than HTML, and multi-user support with authentication.

---

## 8. Governance & Workflow

- **Version control**: `main` is the integration branch, and all changes reach it through pull requests, with no direct commits. Unrelated work never goes on an in-flight pull request; each concern gets its own branch and pull request.
- **Commits**: Conventional Commits with the `[FR][WI][TASK]` suffix, enforced by a `commit-msg` hook in the `pre-commit` framework (Python). `gitleaks` is the secret scanner run by hooks and CI.
- **CI**: Gates run in this order in `.github/workflows/validators.yml`: gitleaks, ruff, mypy, ESLint and Prettier, tsc, pytest, Vitest. The fork has no `validators.yml` yet, so one is added. The existing OpenUI workflows in `.github/workflows/` stay in the repository and are disabled on the fork in GitHub.
- **Tool configuration**: Canonical configuration files are `pyproject.toml` for ruff, mypy and pytest, the ESLint flat config, and the Prettier config for the frontend. Backend tests live in `tests/` mirroring `app/`. Frontend tests sit beside the code. Fixtures live in `tests/fixtures`.
- **Coding agent**: Claude Code. Its `CLAUDE.md` exists locally and is listed in `.gitignore`, so it is not tracked in Git. There is no init command. `CLAUDE.md` references `docs/PRODUCT.md`, `adr.md`, `config.yaml` and `.sdd/constitution.md`.
- **Agent limits**: An agent needs approval before adding or upgrading a dependency, changing the database schema, or expanding scope beyond the requirements. It does not rebase, amend pushed commits or force-push without approval. After pushing, an agent leaves the working tree on the pushed pull request branch.
- **Naming**: The button labels "Generate Report", "Download Report", "Erase History" and "Erase Report" must not be renamed.
- **Governance**: Initial constitution version `1.0.0`, ratified on the date `docs/PRODUCT.md` is approved. Amendments are logged in `CHANGELOG.md`.

---

## 9. Approval

- **Approved by**: Gabriel Munera (gamug)
- **First approved on**: 2026-11-05
- **Approved on**: 2026-11-05
- **Approved content**: sha256:71ebbff4a0c59f2c0dd987063d345577cd84288e3690893b1ff15fe7676fc75b

## Configuration Decisions

Source is `PRODUCT.md § <section>` (an existing heading, or its number, with no
subsections and whose text contains the value) or `user, YYYY-MM-DD` for
values the user decided or confirmed. Lists and maps are recorded as compact JSON; escape `|` as `\|`.

| Key | Value | Source |
| :--- | :--- | :--- |
| `agent.destructive_history_boundary` | {"rebase":"needs approval","amend of pushed commits":"needs approval","force-push":"needs approval"} | user, 2026-11-05 |
| `agent.init_command_if_missing` | bash scripts/init.sh | user, 2026-11-06 |
| `agent.instruction_file` | CLAUDE.md | PRODUCT.md § 8 |
| `agent.leave_on_pr_branch` | yes | user, 2026-11-05 |
| `agent.must_exist` | yes, locally | user, 2026-11-05 |
| `agent.must_reference` | ["docs/PRODUCT.md","adr.md","config.yaml",".sdd/constitution.md"] | PRODUCT.md § 8 |
| `agent.scope_expansion_requires_approval` | ["adding or upgrading a dependency","changing the database schema","expanding scope beyond the requirements"] | PRODUCT.md § 8 |
| `agent.tracked` | no, it is listed in .gitignore | user, 2026-11-05 |
| `code_git.direct_commits_to_integration_branch` | no | user, 2026-11-05 |
| `code_git.unrelated_work_on_inflight_pr` | not allowed; each concern gets its own branch and pull request | user, 2026-11-05 |
| `commands.ci_test` | uv run --directory backend pytest && pnpm --dir frontend test --run | user, 2026-11-05 |
| `commands.dependency_install` | uv sync --locked --directory backend && pnpm --dir frontend install --frozen-lockfile | user, 2026-11-05 |
| `commands.format_check` | uv run --directory backend ruff format --check . && pnpm --dir frontend exec prettier --check . | user, 2026-11-05 |
| `commands.lint` | uv run --directory backend ruff check . && pnpm --dir frontend lint | user, 2026-11-05 |
| `commands.pre_commit` | uv run --directory backend pre-commit run --all-files | user, 2026-11-05 |
| `commands.test` | uv run --directory backend pytest && pnpm --dir frontend test --run | user, 2026-11-05 |
| `commands.type_check` | uv run --directory backend mypy app && pnpm --dir frontend exec tsc --noEmit | user, 2026-11-05 |
| `domain_sections` | [{"title":"Chat and knowledge-graph access","rules":["The chat reaches GraphDB only through the backend connector; the browser never holds GraphDB or DeepSeek credentials.","The connector uses a read-only GraphDB user, never a write-enabled or admin user (RSK-007).","The tool loop has a bounded number of iterations; a failed question is shown as an error and never stored (FR-004)."]},{"title":"Sessions and persistence","rules":["SQLite is the only store; sessions follow the OpenUI thread REST convention (adr-005).","Erase and delete actions ask for confirmation and apply to the active session only (FR-033, FR-034).","A database error is shown and leaves the visible state unchanged (FR-011); schema changes are migration-driven and need approval."]},{"title":"Report generation and export","rules":["Only question-answer pairs marked as relevant feed a report; generation streams, can be cancelled, and disables the chat (FR-013 to FR-019).","The report is stored as OpenUI Lang, one current report per session (adr-009).","Download is one self-contained HTML file named <session-name>-<YYYY-MM-DD>.html with no external resources."]},{"title":"LLM usage and accuracy","rules":["DeepSeek is the only LLM; its key lives in .env and the OpenUI prompt is generated locally (adr-006).","The interface and reports follow the analyst's language (FR-035).","The curated question set must reach 90% correct answers."]}] | user, 2026-11-05 |
| `governance.amendment_log_source` | .sdd/CHANGELOG.md | user, 2026-11-05 |
| `governance.last_amended` | 2026-11-05 | user, 2026-11-05 |
| `governance.ratified` | 2026-11-05 | user, 2026-11-05 |
| `governance.version` | 1.0.0 | PRODUCT.md § 8 |
| `known_constraints` | ["The MVP is built in 1 week; the spike runs on days 1-2.","Data leaves the machine only to GraphDB and DeepSeek; secrets live in .env and are never committed.","Out of the MVP: manual report editing, chart property editing, report tweaks through the chat, formats other than HTML, multi-user support and authentication.","Chat per-pair controls, DeepSeek tool calling, OpenUI Lang validity and bundle inlining are verified in the first spike (RSK-001 to RSK-004)."] | user, 2026-11-05 |
| `naming.mappings` | {"report generation action":"Generate Report","report download action":"Download Report","history erase action":"Erase History","report erase action":"Erase Report"} | user, 2026-11-05 |
| `project.excluded_components` | ["manual report editing","chart property editing","report tweaks through the chat","report formats other than HTML","multi-user support and authentication"] | user, 2026-11-05 |
| `project.integration_branch` | main | PRODUCT.md § 8 |
| `project.kind` | Local single-user web application (FastAPI backend, Vite + React frontend) | user, 2026-11-05 |
| `project.name` | portfolio-app-new | PRODUCT.md § 6 |
| `project.source_dir` | backend/app and frontend/src | user, 2026-11-05 |
| `project.tests_dir` | backend/tests and frontend/src | user, 2026-11-05 |
| `project_structure.config` | {"python tools":"backend/pyproject.toml (ruff, mypy, pytest)","frontend tools":"the ESLint flat config and the Prettier config in frontend/","git hooks":".pre-commit-config.yaml","environment":".env.example (committed) and .env (local, untracked)","devcontainer":".devcontainer/devcontainer.json","secret scanner":".gitleaks.toml"} | user, 2026-11-05 |
| `project_structure.tests` | {"backend":"backend/tests mirroring backend/app","frontend":"tests beside the code in frontend/src","fixtures":"backend/tests/fixtures; small, committed, hermetic, with no real graph data or secrets"} | user, 2026-11-05 |
| `quality.ci_file` | .github/workflows/validators.yml | PRODUCT.md § 8 |
| `quality.ci_gate_order` | ["gitleaks","ruff","mypy","ESLint and Prettier","tsc","pytest","Vitest"] | PRODUCT.md § 8 |
| `quality.commit_hook` | a `commit-msg` hook in the `pre-commit` framework (Python) | PRODUCT.md § 8 |
| `quality.secret_scanner` | gitleaks | PRODUCT.md § 8 |
| `runtime.dependency_manifest` | backend/pyproject.toml and frontend/package.json | user, 2026-11-05 |
| `runtime.language` | Python (backend) and Node.js (frontend) | user, 2026-11-05 |
| `runtime.lockfile` | backend/uv.lock and frontend/pnpm-lock.yaml | user, 2026-11-05 |
| `runtime.package_manager` | uv and pnpm | user, 2026-11-05 |
| `runtime.version` | 3.12 and 22.12 | user, 2026-11-05 |
