# portfolio-app-new

A chat interface to a GraphDB knowledge graph, with a report panel beside it. The analyst chats with the graph, marks the useful question-answer pairs, presses **Generate Report**, and downloads the result as one self-contained HTML file. The report view is built on [OpenUI](https://github.com/thesysdev/openui); this repository is a fork of `thesysdev/openui` (MIT, see `LICENSE`).

The project follows specification-driven development:

| Path | Content |
| :--- | :--- |
| `docs/PRODUCT.md` | Approved discovery: use cases, requirements, stack, risks and roadmap |
| `adr.md` | Architecture decision records (live) |
| `config.yaml` | Project configuration, with sources in `docs/PRODUCT.md` |
| `.sdd/` | Constitution, specification, plan, tasks and changelog |
| `backend/` | FastAPI backend (`app/`, `tests/`) |
| `frontend/` | Vite + React frontend |
| `packages/`, `examples/`, `spec/` | OpenUI source, examples and language specification, kept for reference |

Setup instructions are added with the environment automation (WI-005 and WI-006).
