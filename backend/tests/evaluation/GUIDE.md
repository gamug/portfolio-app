# Guide: preparing the evaluation questions

**For:** dova (and gamug), who prepare the question set together.
**Goal:** a file of questions about the knowledge graph, each with a known correct answer, that we use to measure whether the chat answers correctly.
**When:** before the technical spike starts (task `TASK-018` in `.sdd/TASKS.md`). Without the file the spike cannot measure anything.

## 1. What the questions are used for

The project's success metric is: **at least 90% of the questions in a curated question set are answered correctly** by the chat. The same questions are used twice:

1. **During the spike (days 1-2):** to try the DeepSeek tool loop on the live graph, see which questions fail and why, and tune the prompts. (Criterion `AC-SPIKE-02`.)
2. **At the end (days 6-7):** to measure the final accuracy against the 90% target. (Criterion `AC-ACC-01`, task `TASK-033`.)

If we tune the prompts on the same questions we later use for the final score, the score looks better than it is. So we split the set in two:

- **Development questions:** used freely while tuning.
- **Held-out questions:** not looked at while tuning; used only for the final score.

## 2. How many questions

The more questions, the more reliable the score, but every question needs a verified answer, so there is a cost. The table shows how precise a score is at different sizes (95% confidence, observed score exactly at the 90% target).

| Questions in the set | Correct needed for 90% | Real accuracy could be anywhere between | One wrong answer moves the score by |
| ---: | ---: | :--- | ---: |
| 20 | 18 | 70% and 97% | 5.0 points |
| 40 | 36 | 77% and 96% | 2.5 points |
| 60 | 54 | 80% and 95% | 1.7 points |
| 100 | 90 | 83% and 94% | 1.0 point |
| 200 | 180 | 85% and 93% | 0.5 points |

**Recommendation**

| Option | Development | Held-out | Held-out allows at most | Comment |
| :--- | ---: | ---: | :--- | :--- |
| Minimum | 20 | 40 | 4 wrong answers | Smallest set I would accept. A 90% result still leaves a real accuracy between about 77% and 96%. |
| **Recommended** | 30 | 70 | 7 wrong answers | Good balance of effort and reliability (about 81% to 95% at a 90% result). |
| Comfortable | 60 | 140 | 14 wrong answers | Only if the graph is rich enough that writing good questions is quick. |

So: **plan for about 100 questions (30 development + 70 held-out); do not go below 60 (20 + 40).**

Effort (an assumption, not a measurement): writing a question and checking its answer in GraphDB takes roughly 10 to 15 minutes. 100 questions is therefore roughly 17 to 25 hours between the two of you, plus the review in section 5. If that is too much for the week, take the minimum and say so; the final result must then be reported with its wide margin.

## 3. What mix of questions

Cover what a business analyst would actually ask. This is a suggested split for 100 questions; adjust it to what the graph contains.

| Type of question | How many | Example shape (replace with real content) |
| :--- | ---: | :--- |
| Single fact lookup | 15 | "What is the value of X for Y?" |
| Counts and aggregations (count, sum, average) | 15 | "How many Y have property X?" |
| Filtered lists and rankings (top N, thresholds) | 15 | "Which are the five Y with the highest X?" |
| Relationships across several entities (multi-hop) | 15 | "Which Z are connected to Y through X?" |
| Comparisons over time or between groups | 10 | "How did X change between A and B?" |
| Results that suit a table or a chart (used by the report) | 10 | "Show X by category" |
| Not in the graph (the right answer is that the data does not exist) | 10 | A question whose answer the graph cannot give |
| Ambiguous or incomplete wording | 10 | A question where the right behaviour is to ask or state an assumption |

Write them the way the analyst would say them, not as database queries. Put 30% of each type in the development group and 70% in the held-out group.

## 4. Rules for each question

- **One clear correct answer.** If two people could reasonably answer differently, rewrite it.
- **Verify the answer yourself** in GraphDB (for example with a SPARQL query in the Workbench) and write in `notes` how you derived it, including the query. Do not copy an answer from the chat.
- **Stable.** Do not ask about data that changes every day, unless you fix the date in the question.
- **Publishable.** This repository is **public** and `questions.json` is committed. Use only facts you both approve for publication. No passwords, no personal data, nothing confidential. If a question needs confidential content, leave it out or reword it with non-sensitive facts.
- **Own words.** Do not write questions by asking the chat itself.

## 5. Review

Each person reviews the other's questions: re-run the query behind each expected answer and mark anything unclear. A question counts only after the second person agrees with the answer. Aim for the second pass to be done before the spike starts.

## 6. The file

Create `backend/tests/evaluation/questions.json`, a list of objects:

```json
[
  {
    "id": "q-001",
    "question": "<the question, in the analyst's words>",
    "expected_answer": "<the known correct answer, as text>",
    "expected_tools": ["sparql_query"],
    "notes": "<how you derived it, the query, the group: development or held-out, the type>"
  }
]
```

| Field | Required | Meaning |
| :--- | :--- | :--- |
| `id` | yes | Unique, for example `q-001` |
| `question` | yes | Exactly as the analyst would ask it |
| `expected_answer` | yes | The correct answer, as text |
| `expected_tools` | no | GraphDB tools a correct answer is expected to use |
| `notes` | no | Derivation, query, group and type |

Mark the group in `notes` (for example `group: development`) until the project agrees on a dedicated field. To check the file: `uv run --directory backend pytest tests/evaluation` (it runs the format test).

## 7. Decisions the two of you must agree on

These are not decided anywhere in the project documents yet:

1. **What counts as "correct"?** Proposal: a person marks each answer pass or fail by comparing it with `expected_answer`; it passes only if every required fact or number is present and nothing in it is wrong. Decide the tolerance for numbers (exact, or a rounding rule) and whether a partly correct answer counts as a fail.
2. **Who grades**, and whether the grader can see which group the question is in. The final grading of the held-out questions is best done by someone who did not tune the prompts.
3. **The negative questions:** what a correct "not in the graph" answer looks like.
4. **The final number of questions** (section 2), given your time.
5. **Which facts are publishable** (section 4).

## 8. Checklist before you commit the file

- [ ] At least 60 questions, ideally about 100, in the agreed split.
- [ ] Every answer verified in GraphDB and reviewed by the other person.
- [ ] No credentials, personal data or confidential content.
- [ ] `id` values are unique; the format test passes.
- [ ] The decisions in section 7 are written down (put them in the notes of the pull request).
