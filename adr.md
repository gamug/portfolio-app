# Architecture Decision Records (ADRs)

Live ADR log. Rules: the constitution's Architecture decisions section. Discovery snapshot: `docs/PRODUCT.md` § 5.

> **Erratum (2026-11-06).** Repository paths cited by the ADRs below, and by the frozen snapshot `docs/PRODUCT.md` § 5, have moved: `packages/`, `examples/` and `spec/` are now under `reference/` (for example `reference/examples/app-frameworks/fastapi`). `templates/` was removed in WI-004; the template cited by `adr-008` is at https://github.com/thesysdev/openui/tree/main/templates/openui-self-hosted. The decisions themselves are unchanged.

### `adr-001`: Use Python with FastAPI for the backend

- **Status**: Accepted
- **Proposed on**: 2026-11-05
- **Approved by**: Gabriel Munera (gamug)
- **Approved on**: 2026-11-05
- **Rejected by**: N/A
- **Rejected on**: N/A
- **Rejection reason**: N/A
- **Deprecated by**: N/A
- **Deprecated on**: N/A
- **Deprecation reason**: N/A
- **Supersedes**: N/A
- **Superseded By**: N/A
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

- **Status**: Accepted
- **Proposed on**: 2026-11-05
- **Approved by**: Gabriel Munera (gamug)
- **Approved on**: 2026-11-05
- **Rejected by**: N/A
- **Rejected on**: N/A
- **Rejection reason**: N/A
- **Deprecated by**: N/A
- **Deprecated on**: N/A
- **Deprecation reason**: N/A
- **Supersedes**: N/A
- **Superseded By**: N/A
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

- **Status**: Accepted
- **Proposed on**: 2026-11-05
- **Approved by**: Gabriel Munera (gamug)
- **Approved on**: 2026-11-05
- **Rejected by**: N/A
- **Rejected on**: N/A
- **Rejection reason**: N/A
- **Deprecated by**: N/A
- **Deprecated on**: N/A
- **Deprecation reason**: N/A
- **Supersedes**: N/A
- **Superseded By**: N/A
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

- **Status**: Accepted
- **Proposed on**: 2026-11-05
- **Approved by**: Gabriel Munera (gamug)
- **Approved on**: 2026-11-05
- **Rejected by**: N/A
- **Rejected on**: N/A
- **Rejection reason**: N/A
- **Deprecated by**: N/A
- **Deprecated on**: N/A
- **Deprecation reason**: N/A
- **Supersedes**: N/A
- **Superseded By**: N/A
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

- **Status**: Accepted
- **Proposed on**: 2026-11-05
- **Approved by**: Gabriel Munera (gamug)
- **Approved on**: 2026-11-05
- **Rejected by**: N/A
- **Rejected on**: N/A
- **Rejection reason**: N/A
- **Deprecated by**: N/A
- **Deprecated on**: N/A
- **Deprecation reason**: N/A
- **Supersedes**: N/A
- **Superseded By**: N/A
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

- **Status**: Accepted
- **Proposed on**: 2026-11-05
- **Approved by**: Gabriel Munera (gamug)
- **Approved on**: 2026-11-05
- **Rejected by**: N/A
- **Rejected on**: N/A
- **Rejection reason**: N/A
- **Deprecated by**: N/A
- **Deprecated on**: N/A
- **Deprecation reason**: N/A
- **Supersedes**: N/A
- **Superseded By**: N/A
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

- **Status**: Superseded
- **Proposed on**: 2026-11-05
- **Approved by**: Gabriel Munera (gamug)
- **Approved on**: 2026-11-05
- **Rejected by**: N/A
- **Rejected on**: N/A
- **Rejection reason**: N/A
- **Deprecated by**: N/A
- **Deprecated on**: N/A
- **Deprecation reason**: N/A
- **Supersedes**: N/A
- **Superseded By**: `adr-010`
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

- **Status**: Accepted
- **Proposed on**: 2026-11-05
- **Approved by**: Gabriel Munera (gamug)
- **Approved on**: 2026-11-05
- **Rejected by**: N/A
- **Rejected on**: N/A
- **Rejection reason**: N/A
- **Deprecated by**: N/A
- **Deprecated on**: N/A
- **Deprecation reason**: N/A
- **Supersedes**: N/A
- **Superseded By**: N/A
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

- **Status**: Accepted
- **Proposed on**: 2026-11-05
- **Approved by**: Gabriel Munera (gamug)
- **Approved on**: 2026-11-05
- **Rejected by**: N/A
- **Rejected on**: N/A
- **Rejection reason**: N/A
- **Deprecated by**: N/A
- **Deprecated on**: N/A
- **Deprecation reason**: N/A
- **Supersedes**: N/A
- **Superseded By**: N/A
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

### `adr-010`: Forward the analyst's question to a Talk to Your Graph agent through the Workbench chat API

- **Status**: Accepted
- **Proposed on**: 2026-11-07
- **Approved by**: dova
- **Approved on**: 2026-11-07
- **Rejected by**: N/A
- **Rejected on**: N/A
- **Rejection reason**: N/A
- **Deprecated by**: N/A
- **Deprecated on**: N/A
- **Deprecation reason**: N/A
- **Supersedes**: `adr-007`
- **Superseded By**: N/A
- **Context**: `adr-007` chose a FastAPI connector that runs DeepSeek as the chat agent over GraphDB's documented tool API, and rejected forwarding the question to a Talk to Your Graph agent because no documented endpoint answers a question. The TASK-018 spike found two things. First, the tool loop is fragile: with no knowledge of the graph schema, DeepSeek generated unfiltered full scans (`?s ?p ?o` with `FILTER(CONTAINS(STR(...)))`) that stayed running in GraphDB after the client gave up, filled the query queue and blocked every later call (the repository `portfolio_test` has no query timeout). Second, the running GraphDB 11.5.1 does expose an undocumented endpoint pair used by its own Workbench chat, which is absent from the instance's OpenAPI description (`/v3/api-docs`): `POST /rest/chat/chats` with `{agentId, question, tzOffset}` creates a conversation and returns its `conversationId`, and `POST /rest/chat/chats/question` with `{agentId, conversationId, question, tzOffset}` returns the complete answer as JSON (`messages[].message`, with `usage`). Both worked from outside the Workbench with the read-only application user (`portfolio.app`, role User, Read on one repository). The existing agent (`reportes-piloto-ds`, DeepSeek model, SPARQL tool only) already carries instructions that describe the data, so it answers with targeted queries. Measured on one question: about 25 s end to end and about 125,000 input tokens (GraphDB reports a lower total than the DeepSeek panel; the project owners state the cost is not a concern).
- **Decision Drivers**:
  - **Business goal**: deliver the MVP in 1 week and answer accurately against the graph.
  - **Technical constraint**: credentials stay on the server; the app user is read-only; the question and the raw answer must be stored and the answer converted to OpenUI Lang.
  - **Quality attribute**: avoid query floods that block GraphDB; keep the data description in one place (the agent) instead of copying the schema into the connector prompt.
- **Considered Options**:
  1. Keep `adr-007`: DeepSeek tool loop over the documented tool API, with the schema in the connector prompt and a repository query timeout
  2. Forward the question to the Talk to Your Graph agent through `/rest/chat/chats` and `/rest/chat/chats/question`, then convert the answer to OpenUI Lang with a second DeepSeek call
  3. Option 2 as the default, keeping option 1 as a fallback behind one setting
- **Decision**: Option 3. The connector creates a chat with `POST /rest/chat/chats`, sends the question with `POST /rest/chat/chats/question` using the app user's credentials, takes the answer text from the response, converts it to OpenUI Lang with a second DeepSeek call, and stores the question, the raw answer and the OpenUI Lang after the answer completes. The agent id, the chat mode and a fallback to the `adr-007` tool loop are settings. The connector checks at startup that both endpoints respond, and reports a clear error when they do not.
- **Consequences (Positive)**: No tool loop, schema prompt or iteration limit to build in the backend; the data description lives in the agent instructions; no model-generated full scans from our code; fewer moving parts for a 1-week MVP.
- **Consequences (Trade-offs)**: The endpoints are internal and undocumented, so a GraphDB upgrade can break them without notice; the answer arrives whole (about 25 s), so streaming to the chat needs a progress state instead of token streaming; the answer language and format follow the agent instructions, so `FR-035` needs the instructions adjusted or a conversion step; about 125,000 input tokens per question; conversations accumulate in the Workbench history unless deleted.
- **Mitigation**: Pin the supported GraphDB version (11.5.1) in the documentation and the startup check; keep the `adr-007` loop as a selectable fallback; set a query timeout on the repository; show a progress state while waiting; delete or reuse the conversation per session; re-run the curated question set (`AC-ACC-01`) on the final graph before accepting this ADR as final.
- **Rejected Options**: Option 1 alone: it needs a schema prompt and guard rails written and maintained in the backend, and it already blocked GraphDB in the spike. Option 2 without a fallback: a single internal API with no documented contract is too fragile to be the only path.
- **Traceability**: `FR-002`, `FR-003`, `FR-004`, `FR-035`; spike `AC-SPIKE-02`; `docs/PRODUCT.md` `RSK-001`
- **External Docs**: `https://graphdb.ontotext.com/documentation/11.5/talk-to-graph.html`; `https://graphdb.ontotext.com/documentation/11.5/using-graphdb-llm-tools-with-external-clients.html`
