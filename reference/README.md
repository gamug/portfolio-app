# reference/

OpenUI source, examples and language specification, kept **for reading only**. This is the upstream code of [thesysdev/openui](https://github.com/thesysdev/openui) (MIT, see `../LICENSE`) at the commit this repository was forked from. The application is in `backend/` and `frontend/`.

| Path | Content |
| :--- | :--- |
| `packages/` | OpenUI packages (`react-lang`, `react-ui`, `react-headless`, `browser-bundle`, ...) |
| `examples/` | OpenUI examples, including the FastAPI example the backend started from |
| `spec/` | The OpenUI Lang specification and conformance fixtures |

The ADRs in `../adr.md` and the approved `../docs/PRODUCT.md` cite these folders as `packages/...`, `examples/...` and `spec/...`; they now live here. `templates/` was removed; the template cited by `adr-008` is at https://github.com/thesysdev/openui/tree/main/templates/openui-self-hosted.

`reference/` has its own pnpm workspace (`package.json`, `pnpm-workspace.yaml`) and is **not** installed, linted, tested or built by this project's hooks or CI. The project depends on the published `@openuidev/*` packages from npm, not on this copy. Only workspace housekeeping was changed here (dangling workspace entries and scripts that called deleted files); the upstream source is untouched.
