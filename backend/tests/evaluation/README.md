# Evaluation question set

The curated question set behind the success metric of `docs/PRODUCT.md` (at least 90% of the questions answered correctly) and the spike criteria `AC-SPIKE-02` and `AC-ACC-01` in `.sdd/SPEC.md`.

- **Owners:** gamug and dova prepare it. It must exist before `TASK-018` (the DeepSeek tool-loop spike) starts.
- **File:** `questions.json`, next to this README: a JSON list of objects.
- **Public repository:** this repository is public and the file is committed, so it may contain **only facts the owners approve for publication**. Do not put credentials, personal data or confidential graph content in it. This is different from `backend/tests/fixtures`, which holds synthetic data only.

Each object has these fields:

| Field | Required | Meaning |
| :--- | :--- | :--- |
| `id` | yes | Unique short identifier, for example `q-001` |
| `question` | yes | The question exactly as the analyst would ask it |
| `expected_answer` | yes | The known correct answer, as text |
| `expected_tools` | no | GraphDB tools a correct answer is expected to use (for example `sparql_query`) |
| `notes` | no | Anything a reviewer needs, for example how the answer was derived |

`test_questions_format.py` checks the file when it exists. It is skipped while `questions.json` has not been prepared.
