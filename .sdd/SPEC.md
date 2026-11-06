# Specification

## Functional requirements

### FR-001 — Discover and initialize the project

The project must complete the ordered Work Items in [`PLAN.md`](./PLAN.md). The hierarchy is strictly:

```text
FR-001
└── Work Items
    └── Tasks
```

FR-001 does not define the project's purpose, scope, product, stack, or architecture in advance. Those decisions are discovered through WI-001 and then applied by the remaining Work Items. FR-001 is reserved for initialization: the product requirements discovered in WI-001 are numbered from `FR-002`, and `validate_discovery.py` rejects an `FR-001` row in `docs/PRODUCT.md`.

### Product functional requirements

The product requirements below are copied from the approved `docs/PRODUCT.md` section 3, which remains their decision source. Requirements marked Won't Have are out of the MVP and have no Work Item.

#### FR-002

- **Statement:** WHEN the analyst submits a question, the system shall send it to DeepSeek through the connector, let DeepSeek query the knowledge graph through the GraphDB LLM tool API, and stream the answer into the chat as it arrives.
- **EARS pattern:** Event-Driven
- **Priority:** Must Have
- **Use cases:** UC-001
- **Acceptance criteria:** AC-FR002-01, AC-FR002-02

#### FR-003

- **Statement:** WHEN an answer completes, the system shall store the question text, the raw answer text and the OpenUI Lang version of the answer as a question-answer pair in the active session, marked as relevant.
- **EARS pattern:** Event-Driven
- **Priority:** Must Have
- **Use cases:** UC-001, UC-009
- **Acceptance criteria:** AC-FR002-01, AC-FR002-02, AC-FR003-01, AC-FR003-02

#### FR-004

- **Statement:** IF GraphDB or DeepSeek is unreachable, returns an error, or the tool loop does not finish, THEN the system shall show an error in the chat and shall not store the failed question.
- **EARS pattern:** Unwanted / Error
- **Priority:** Must Have
- **Use cases:** UC-001
- **Acceptance criteria:** AC-FR002-01, AC-FR002-02

#### FR-005

- **Statement:** The system shall persist sessions, chat history, relevance marks and reports in a SQLite database so that they survive application restarts.
- **EARS pattern:** Ubiquitous
- **Priority:** Must Have
- **Use cases:** UC-001, UC-002, UC-003, UC-009
- **Acceptance criteria:** AC-FR005-01, AC-FR005-02, AC-FR005-03, AC-FR005-04

#### FR-006

- **Statement:** WHEN the analyst creates a session, the system shall make it the active session with an empty history and no report.
- **EARS pattern:** Event-Driven
- **Priority:** Must Have
- **Use cases:** UC-002
- **Acceptance criteria:** AC-FR005-01, AC-FR005-02, AC-FR005-03, AC-FR005-04

#### FR-007

- **Statement:** WHEN the analyst selects a session, the system shall make it the active session and load its chat history and current report.
- **EARS pattern:** Event-Driven
- **Priority:** Must Have
- **Use cases:** UC-002
- **Acceptance criteria:** AC-FR005-01, AC-FR005-02, AC-FR005-03, AC-FR005-04

#### FR-008

- **Statement:** WHEN the analyst renames a session, the system shall store the new name.
- **EARS pattern:** Event-Driven
- **Priority:** Must Have
- **Use cases:** UC-002
- **Acceptance criteria:** AC-FR005-01, AC-FR005-02, AC-FR005-03, AC-FR005-04

#### FR-009

- **Statement:** WHEN the analyst confirms deleting a session, the system shall delete the session with its history and report.
- **EARS pattern:** Event-Driven
- **Priority:** Must Have
- **Use cases:** UC-002
- **Acceptance criteria:** AC-FR005-01, AC-FR005-02, AC-FR005-03, AC-FR005-04

#### FR-010

- **Statement:** IF the deleted session was the active session, THEN the system shall create a new empty session and make it the active session.
- **EARS pattern:** Unwanted / Error
- **Priority:** Must Have
- **Use cases:** UC-002
- **Acceptance criteria:** AC-FR005-01, AC-FR005-02, AC-FR005-03, AC-FR005-04

#### FR-011

- **Statement:** IF the database cannot be read or written, THEN the system shall show an error and leave the visible state unchanged.
- **EARS pattern:** Unwanted / Error
- **Priority:** Must Have
- **Use cases:** UC-002, UC-004, UC-009
- **Acceptance criteria:** AC-FR005-01, AC-FR005-02, AC-FR005-03, AC-FR005-04

#### FR-012

- **Statement:** WHEN the analyst switches the relevance toggle of a question-answer pair, the system shall store the new relevance state of the pair.
- **EARS pattern:** Event-Driven
- **Priority:** Must Have
- **Use cases:** UC-009
- **Acceptance criteria:** AC-FR003-01, AC-FR003-02

#### FR-013

- **Statement:** WHEN the analyst presses "Generate Report" and the active session has at least one pair marked as relevant, the system shall pass the marked pairs to the report agent and stream the report progressively into the report panel.
- **EARS pattern:** Event-Driven
- **Priority:** Must Have
- **Use cases:** UC-003
- **Acceptance criteria:** AC-FR013-01, AC-FR013-02, AC-FR013-03, AC-FR013-04, AC-FR013-05, AC-FR013-06

#### FR-014

- **Statement:** IF the analyst presses "Generate Report" and the active session has no history, THEN the system shall not generate and shall ask the analyst to start the data exploration first.
- **EARS pattern:** Unwanted / Error
- **Priority:** Must Have
- **Use cases:** UC-003
- **Acceptance criteria:** AC-FR013-01, AC-FR013-02, AC-FR013-03, AC-FR013-04, AC-FR013-05, AC-FR013-06

#### FR-015

- **Statement:** IF the analyst presses "Generate Report" and the active session has history but no pair marked as relevant, THEN the system shall not generate and shall ask the analyst to mark at least one pair.
- **EARS pattern:** Unwanted / Error
- **Priority:** Must Have
- **Use cases:** UC-003
- **Acceptance criteria:** AC-FR013-01, AC-FR013-02, AC-FR013-03, AC-FR013-04, AC-FR013-05, AC-FR013-06

#### FR-016

- **Statement:** WHILE a report is being generated, the system shall disable the chat and show a progress indication.
- **EARS pattern:** State-Driven
- **Priority:** Must Have
- **Use cases:** UC-003
- **Acceptance criteria:** AC-FR013-01, AC-FR013-02, AC-FR013-03, AC-FR013-04, AC-FR013-05, AC-FR013-06

#### FR-017

- **Statement:** WHEN the analyst cancels a report generation, the system shall stop it, keep the previous report if any, and re-enable the chat.
- **EARS pattern:** Event-Driven
- **Priority:** Must Have
- **Use cases:** UC-003
- **Acceptance criteria:** AC-FR013-01, AC-FR013-02, AC-FR013-03, AC-FR013-04, AC-FR013-05, AC-FR013-06

#### FR-018

- **Statement:** WHEN a report generation completes, the system shall store the report as the current report of the session, replacing any previous report.
- **EARS pattern:** Event-Driven
- **Priority:** Must Have
- **Use cases:** UC-003
- **Acceptance criteria:** AC-FR013-01, AC-FR013-02, AC-FR013-03, AC-FR013-04, AC-FR013-05, AC-FR013-06

#### FR-019

- **Statement:** IF the report agent fails during generation, THEN the system shall show an error, keep the partial report as the current report flagged as incomplete, and re-enable the chat.
- **EARS pattern:** Unwanted / Error
- **Priority:** Must Have
- **Use cases:** UC-003
- **Acceptance criteria:** AC-FR013-01, AC-FR013-02, AC-FR013-03, AC-FR013-04, AC-FR013-05, AC-FR013-06

#### FR-020

- **Statement:** WHEN the analyst regenerates a report that has manual edits, the system shall warn that regeneration overwrites the edits and continue only after confirmation.
- **EARS pattern:** Event-Driven
- **Priority:** Won't Have
- **Use cases:** UC-003, UC-004
- **Acceptance criteria:** none (Won't Have)

#### FR-021

- **Statement:** The system shall build each report from plots, tables of the returned data and narrative text that together tell a story with the data.
- **EARS pattern:** Ubiquitous
- **Priority:** Must Have
- **Use cases:** UC-003
- **Acceptance criteria:** AC-FR013-01, AC-FR013-02, AC-FR013-03, AC-FR013-04, AC-FR013-05, AC-FR013-06, AC-FR021-01

#### FR-022

- **Statement:** The system shall show the chat panel and the report panel side by side.
- **EARS pattern:** Ubiquitous
- **Priority:** Must Have
- **Use cases:** UC-003
- **Acceptance criteria:** AC-FR013-01, AC-FR013-02, AC-FR013-03, AC-FR013-04, AC-FR013-05, AC-FR013-06

#### FR-023

- **Statement:** WHEN the analyst edits a narrative text block of the current report, the system shall update the report panel and store the edited report.
- **EARS pattern:** Event-Driven
- **Priority:** Won't Have
- **Use cases:** UC-004
- **Acceptance criteria:** none (Won't Have)

#### FR-024

- **Statement:** WHEN the analyst reorders or removes a section of the current report, the system shall update the report panel and store the edited report.
- **EARS pattern:** Event-Driven
- **Priority:** Won't Have
- **Use cases:** UC-004
- **Acceptance criteria:** none (Won't Have)

#### FR-025

- **Statement:** WHILE the active session has no report, the system shall not offer report editing controls.
- **EARS pattern:** State-Driven
- **Priority:** Won't Have
- **Use cases:** UC-004
- **Acceptance criteria:** none (Won't Have)

#### FR-026

- **Statement:** WHEN the analyst presses "Download Report" and the session has a report, the system shall download one self-contained HTML file named `<session-name>-<YYYY-MM-DD>.html`.
- **EARS pattern:** Event-Driven
- **Priority:** Must Have
- **Use cases:** UC-005
- **Acceptance criteria:** AC-FR026-01, AC-FR026-02

#### FR-027

- **Statement:** IF the analyst presses "Download Report" and the session has no report, THEN the system shall not download and shall tell the analyst to generate a report first.
- **EARS pattern:** Unwanted / Error
- **Priority:** Must Have
- **Use cases:** UC-005
- **Acceptance criteria:** AC-FR026-01, AC-FR026-02

#### FR-028

- **Statement:** WHEN the analyst confirms "Erase History", the system shall erase all question-answer pairs and the report of the active session.
- **EARS pattern:** Event-Driven
- **Priority:** Must Have
- **Use cases:** UC-006
- **Acceptance criteria:** AC-FR028-01, AC-FR028-02, AC-FR028-03, AC-FR028-04, AC-FR028-05

#### FR-029

- **Statement:** WHILE the active session has no history, the system shall disable "Erase History".
- **EARS pattern:** State-Driven
- **Priority:** Must Have
- **Use cases:** UC-006
- **Acceptance criteria:** AC-FR028-01, AC-FR028-02, AC-FR028-03, AC-FR028-04, AC-FR028-05

#### FR-030

- **Statement:** WHEN the analyst confirms "Erase Report", the system shall erase the report of the active session and keep its history.
- **EARS pattern:** Event-Driven
- **Priority:** Must Have
- **Use cases:** UC-007
- **Acceptance criteria:** AC-FR028-01, AC-FR028-02, AC-FR028-03, AC-FR028-04, AC-FR028-05

#### FR-031

- **Statement:** WHILE the active session has no report, the system shall disable "Erase Report".
- **EARS pattern:** State-Driven
- **Priority:** Must Have
- **Use cases:** UC-007
- **Acceptance criteria:** AC-FR028-01, AC-FR028-02, AC-FR028-03, AC-FR028-04, AC-FR028-05

#### FR-032

- **Statement:** WHEN the analyst confirms deleting a question-answer pair, the system shall delete the pair from the active session and leave the current report unchanged.
- **EARS pattern:** Event-Driven
- **Priority:** Must Have
- **Use cases:** UC-008
- **Acceptance criteria:** AC-FR028-01, AC-FR028-02, AC-FR028-03, AC-FR028-04, AC-FR028-05

#### FR-033

- **Statement:** The system shall ask for confirmation before deleting a session, a question-answer pair, a history or a report, and shall change nothing when the analyst declines.
- **EARS pattern:** Ubiquitous
- **Priority:** Must Have
- **Use cases:** UC-002, UC-006, UC-007, UC-008
- **Acceptance criteria:** AC-FR028-01, AC-FR028-02, AC-FR028-03, AC-FR028-04, AC-FR028-05

#### FR-034

- **Statement:** The system shall apply every erase and delete action to the active session only.
- **EARS pattern:** Ubiquitous
- **Priority:** Must Have
- **Use cases:** UC-002, UC-006, UC-007, UC-008
- **Acceptance criteria:** AC-FR028-01, AC-FR028-02, AC-FR028-03, AC-FR028-04, AC-FR028-05

#### FR-035

- **Statement:** The system shall write the interface text and the generated reports in the language the analyst writes in.
- **EARS pattern:** Ubiquitous
- **Priority:** Must Have
- **Use cases:** UC-001, UC-003
- **Acceptance criteria:** AC-FR002-01, AC-FR002-02, AC-FR035-01

## Acceptance criteria

Each criterion uses the constitution's executable GIVEN-WHEN-THEN form. A criterion may have several scenarios under the same ID.

- **AC-FR001-01:**

  ```gherkin
  SCENARIO: Discovery package approved
    GIVEN the discovery phases are complete
    WHEN the user approves `docs/PRODUCT.md`
    THEN it contains the complete discovery package
    AND it has no unresolved decisions
    AND it records the user's approval
    AND `validate_discovery.py` passes without `--draft`
  ```

  ```gherkin
  SCENARIO: Discovery ADRs accepted
    GIVEN `docs/PRODUCT.md` is approved
    WHEN the seeded ADRs are accepted
    THEN the root `adr.md` holds the discovery ADRs
    AND each is `Accepted` with `Approved by` and `Approved on` filled from the approver and first approval date recorded in `docs/PRODUCT.md`
  ```

- **AC-FR001-02:**

  ```gherkin
  SCENARIO: Configuration built
    GIVEN an approved `docs/PRODUCT.md`
    WHEN root `config.yaml` is built
    THEN it defines every key the constitution template requires
    AND each value's source (`PRODUCT.md § <section>` or `user, YYYY-MM-DD`) is recorded in the `Configuration Decisions` table of `docs/PRODUCT.md`
    AND `validate_config.py check` passes
  ```

- **AC-FR001-03:**

  ```gherkin
  SCENARIO: Constitution rendered
    GIVEN a `config.yaml` that passes `validate_config.py check`
    WHEN `validate_config.py render` runs
    THEN `.sdd/constitution.md` has no placeholders left
  ```

  ```gherkin
  SCENARIO: SDD objects synchronized
    GIVEN a rendered `.sdd/constitution.md`
    WHEN the other canonical `.sdd/` artifacts are created
    THEN they are synchronized with `docs/PRODUCT.md`
  ```

- **AC-FR001-04:**

  ```gherkin
  SCENARIO: Project structure created
    GIVEN the approved constitution and `docs/PRODUCT.md`
    WHEN the project structure is created
    THEN the approved project structure and non-programmatic dependencies exist
    AND no product source code has been implemented
  ```

- **AC-FR001-05:**

  ```gherkin
  SCENARIO: Environment created
    GIVEN the approved project structure exists
    WHEN the selected development environment is created
    THEN its documented baseline checks pass without committed secrets
  ```

- **AC-FR001-06:**

  ```gherkin
  SCENARIO: Environment reproduced
    GIVEN a clean checkout and every documented prerequisite
    WHEN the environment initialization is run
    THEN it reproduces the documented setup
  ```

  ```gherkin
  SCENARIO: Missing prerequisite reported
    GIVEN a clean checkout missing a documented prerequisite
    WHEN the environment initialization is run
    THEN it reports an actionable error
  ```

### Product acceptance criteria

Most criteria below are scenarios of a user story in `docs/PRODUCT.md` section 3 (identifier `AC-FR<primary requirement>-NN`, numbered per story); the user story `US-005` (manual report editing) is Won't Have and has none. The criteria `AC-FR021-01`, `AC-FR035-01`, `AC-ACC-01` and `AC-SPIKE-01` to `AC-SPIKE-06` are **derived** by the SDD team from requirements, the success metric and the risks; they are not user story scenarios and are listed in `PLAN.md` among the deviations to confirm at the next re-approval of `docs/PRODUCT.md`.

- **AC-FR002-01:** from US-001 (Chat with the knowledge graph)

  ```gherkin
  SCENARIO 1: Successful question
    GIVEN an active session
    WHEN the analyst submits a question
    THEN the answer streams into the chat
    AND the question-answer pair is stored in the session, marked as relevant
  ```

- **AC-FR002-02:** from US-001 (Chat with the knowledge graph)

  ```gherkin
  SCENARIO 2: Agent error
    GIVEN an active session
    WHEN the agent is unreachable or returns an error
    THEN the chat shows an error
    AND the failed question is not stored
  ```

- **AC-FR005-01:** from US-002 (Keep my work in sessions)

  ```gherkin
  SCENARIO 1: Switch session
    GIVEN two sessions with different histories
    WHEN the analyst selects the other session
    THEN its history and report are shown
  ```

- **AC-FR005-02:** from US-002 (Keep my work in sessions)

  ```gherkin
  SCENARIO 2: Delete the active session
    GIVEN an active session and the analyst confirms deleting it
    WHEN the deletion completes
    THEN the session, its history and its report no longer exist
    AND a new empty session is active
  ```

- **AC-FR005-03:** from US-002 (Keep my work in sessions)

  ```gherkin
  SCENARIO 3: Restart
    GIVEN sessions with history and reports
    WHEN the application restarts
    THEN the sessions, histories and reports are available
  ```

- **AC-FR005-04:** from US-002 (Keep my work in sessions)

  ```gherkin
  SCENARIO 4: Database error
    GIVEN a database that cannot be written
    WHEN the analyst renames a session
    THEN an error is shown
    AND the visible state is unchanged
  ```

- **AC-FR003-01:** from US-003 (Choose what goes into the report)

  ```gherkin
  SCENARIO 1: Default state
    GIVEN a new question-answer pair
    WHEN it is stored
    THEN it is marked as relevant
  ```

- **AC-FR003-02:** from US-003 (Choose what goes into the report)

  ```gherkin
  SCENARIO 2: Unmark a pair
    GIVEN a pair marked as relevant
    WHEN the analyst switches its toggle
    THEN the pair is stored as not relevant
    AND the current report is unchanged
  ```

- **AC-FR013-01:** from US-004 (Generate a report from the exploration)

  ```gherkin
  SCENARIO 1: Successful generation
    GIVEN a session with at least one pair marked as relevant
    WHEN the analyst presses "Generate Report"
    THEN the chat is disabled and progress is shown
    AND the report streams into the report panel beside the chat
    AND the report becomes the session's current report
  ```

- **AC-FR013-02:** from US-004 (Generate a report from the exploration)

  ```gherkin
  SCENARIO 2: No history
    GIVEN a session with no history
    WHEN the analyst presses "Generate Report"
    THEN the system asks the analyst to start the data exploration
    AND no generation starts
  ```

- **AC-FR013-03:** from US-004 (Generate a report from the exploration)

  ```gherkin
  SCENARIO 3: Nothing marked
    GIVEN a session with history and no pair marked as relevant
    WHEN the analyst presses "Generate Report"
    THEN the system asks the analyst to mark at least one pair
  ```

- **AC-FR013-04:** from US-004 (Generate a report from the exploration)

  ```gherkin
  SCENARIO 4: Cancel
    GIVEN a generation in progress and a previous report
    WHEN the analyst cancels
    THEN the previous report is kept
    AND the chat is enabled
  ```

- **AC-FR013-05:** from US-004 (Generate a report from the exploration)

  ```gherkin
  SCENARIO 5: Agent failure
    GIVEN a generation in progress
    WHEN the report agent fails
    THEN an error is shown
    AND the partial report is the current report, flagged incomplete
  ```

- **AC-FR013-06:** from US-004 (Generate a report from the exploration)

  ```gherkin
  SCENARIO 6: Regenerate over an existing report
    GIVEN a session with a current report and at least one pair marked as relevant
    WHEN the analyst presses "Generate Report"
    THEN the report is rebuilt from the marked pairs
    AND replaces the previous report
  ```

- **AC-FR026-01:** from US-006 (Download the report)

  ```gherkin
  SCENARIO 1: Download
    GIVEN a session named "Q3 sales" with a report
    WHEN the analyst presses "Download Report" on 2026-11-05
    THEN one HTML file named "Q3 sales-2026-11-05.html" is downloaded
    AND it opens offline with its charts, styles and data
  ```

- **AC-FR026-02:** from US-006 (Download the report)

  ```gherkin
  SCENARIO 2: No report
    GIVEN a session with no report
    WHEN the analyst presses "Download Report"
    THEN no file is downloaded
    AND the system tells the analyst to generate a report first
  ```

- **AC-FR028-01:** from US-007 (Erase history, report or a single answer)

  ```gherkin
  SCENARIO 1: Erase history
    GIVEN a session with history and a report
    WHEN the analyst confirms "Erase History"
    THEN the history and the report of that session are erased
    AND other sessions are unchanged
  ```

- **AC-FR028-02:** from US-007 (Erase history, report or a single answer)

  ```gherkin
  SCENARIO 2: Erase report only
    GIVEN a session with history and a report
    WHEN the analyst confirms "Erase Report"
    THEN the report is erased
    AND the history is kept
  ```

- **AC-FR028-03:** from US-007 (Erase history, report or a single answer)

  ```gherkin
  SCENARIO 3: Delete one pair
    GIVEN a session with a report and several pairs
    WHEN the analyst confirms deleting one pair
    THEN only that pair is removed
    AND the report is unchanged
  ```

- **AC-FR028-04:** from US-007 (Erase history, report or a single answer)

  ```gherkin
  SCENARIO 4: Declined confirmation
    GIVEN any erase or delete action
    WHEN the analyst declines the confirmation
    THEN nothing changes
  ```

- **AC-FR028-05:** from US-007 (Erase history, report or a single answer)

  ```gherkin
  SCENARIO 5: Nothing to erase
    GIVEN a session with no history and no report
    WHEN the analyst looks at the buttons
    THEN "Erase History" and "Erase Report" are disabled
  ```

- **AC-FR021-01:** derived from FR-021 (not a user story scenario)

  ```gherkin
  SCENARIO: Report content
    GIVEN a session with at least one pair marked as relevant
    WHEN a report is generated
    THEN the report contains plots, tables of the returned data and narrative text
    AND together they tell a story with the data
  ```

- **AC-FR035-01:** derived from FR-035 (not a user story scenario)

  ```gherkin
  SCENARIO: Language follows the analyst
    GIVEN the analyst writes questions in a given language
    WHEN the answer is shown and a report is generated
    THEN the interface text and the report are written in that language
  ```

- **AC-ACC-01:** derived from the success metric in `docs/PRODUCT.md` section 1

  ```gherkin
  SCENARIO: Answer accuracy
    GIVEN the curated question set with known correct answers prepared by the project owners
    WHEN every question is asked through the chat
    THEN at least 90% of the questions are answered correctly
  ```

- **AC-SPIKE-01:** derived from RSK-007 (spike exit criterion)

  ```gherkin
  SCENARIO: Read-only application user and tool source
    GIVEN a read-only GraphDB user in `KG_USER` and a configured tool source (`ttyg` or `yaml`)
    WHEN the tool list is requested through `GET /rest/llm/tool/{configType}/{configId}`
    THEN it lists the enabled tools
    AND the application user has no write rights on the repository
  ```

- **AC-SPIKE-02:** derived from RSK-001 (spike exit criterion)

  ```gherkin
  SCENARIO: DeepSeek tool loop
    GIVEN the curated question set and the GraphDB tools
    WHEN a DeepSeek tool loop answers the questions
    THEN the accuracy and the failure modes are recorded
    AND an ADR change is proposed if the 90% target looks out of reach
  ```

- **AC-SPIKE-03:** derived from RSK-002 (spike exit criterion)

  ```gherkin
  SCENARIO: Valid OpenUI Lang
    GIVEN the locally generated OpenUI system prompt
    WHEN DeepSeek generates answers and a report
    THEN the share of output that parses without errors is recorded
  ```

- **AC-SPIKE-04:** derived from RSK-003 (spike exit criterion)

  ```gherkin
  SCENARIO: Per-pair controls in the chat
    GIVEN the react-ui chat layout
    WHEN a relevance toggle and a delete action are added to each question-answer pair
    THEN either they work, or a superseding ADR proposes `@openuidev/react-headless` with a custom UI
  ```

- **AC-SPIKE-05:** derived from RSK-004 (spike exit criterion)

  ```gherkin
  SCENARIO: Self-contained export
    GIVEN a report stored as OpenUI Lang
    WHEN the OpenUI browser bundle and the report are inlined into one HTML file
    THEN the file opens offline without external resources
    AND its size is recorded
  ```

- **AC-SPIKE-06:** derived from RSK-006 (spike exit criterion)

  ```gherkin
  SCENARIO: Plot quality from answer text
    GIVEN stored answer text only
    WHEN the report agent builds plots
    THEN the plot quality is assessed
    AND an ADR is proposed to also store structured tool results if the quality is weak
  ```

## Traceability

- FR-001 contains WI-001 through WI-006.
- WI-001 through WI-006 implement `AC-FR001-01` through `AC-FR001-06`, respectively.
- The product requirements `FR-002` to `FR-035` are implemented by WI-007 through WI-014 (see [`PLAN.md`](./PLAN.md)); `FR-020`, `FR-023`, `FR-024` and `FR-025` are Won't Have.
- Each WI contains its own implementation tasks in [`TASKS.md`](./TASKS.md).
- Every task must identify exactly one parent WI.
- Every task must reference the acceptance-criteria ID it implements.
- No task may exist without a WI, and no WI may exist without a parent functional requirement.
