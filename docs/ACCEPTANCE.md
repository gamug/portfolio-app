# Acceptance verification

Date: 2026-11-08
Scope: TASK-034, WI-014. This matrix links every acceptance criterion listed in TASK-034 to an automated test. TASK-033 (answer accuracy against the curated question set) is deferred to the final knowledge-graph repository and final `backend/tests/evaluation/questions.json`; it is not part of this matrix.

The automated suite uses a temporary SQLite database for backend tests and mocked HTTP, SSE and LLM clients for frontend/report tests. It makes no real GraphDB or DeepSeek calls. Every test in the matrix passed in the TASK-034 run: **158 backend passed, 1 skipped; 88 frontend passed**.

## Traceability matrix

| Acceptance criterion | What it verifies | Automated test(s) |
| :--- | :--- | :--- |
| `AC-FR002-01` | A successful question streams and its pair is stored as relevant | `backend/tests/connector/test_service.py::test_answer_and_store_runs_answer_then_conversion_then_store`<br>`frontend/src/sessions/SessionController.test.ts::SessionController chat > streams the raw answer and reloads the stored OpenUI pair` |
| `AC-FR002-02` | An agent error is shown and the failed question is not stored | `backend/tests/connector/test_service.py::test_answer_failure_does_not_convert_or_store`<br>`frontend/src/sessions/SessionController.test.ts::SessionController chat > shows the localized backend error and does not add the failed question` |
| `AC-FR003-01` | A new pair is stored as relevant by default | `backend/tests/connector/test_service.py::test_answer_and_store_runs_answer_then_conversion_then_store`<br>`backend/tests/storage/test_sqlite_store.py::test_save_and_list_survive_a_new_store_instance` |
| `AC-FR003-02` | Unmarking a pair persists the new relevance and leaves the report unchanged | `frontend/src/sessions/SessionController.test.ts::SessionController relevance > toggles a pair, persists the new state and keeps the report unchanged` |
| `AC-FR005-01` | Selecting another session shows its history and report | `backend/tests/api/test_threads.py::test_two_sessions_keep_separate_histories_and_reports`<br>`frontend/src/sessions/SessionController.test.ts::selects another session and shows its history and report` |
| `AC-FR005-02` | Deleting the active session removes it and leaves a new empty session active | `backend/tests/api/test_threads.py::test_thread_lifecycle_history_report_and_relevance`<br>`backend/tests/storage/test_sqlite_store.py::test_session_delete_cascades_to_pairs_relevance_and_reports`<br>`frontend/src/sessions/SessionController.test.ts::creates and selects a new empty session after deleting the active one` |
| `AC-FR005-03` | Sessions, history and reports survive a restart | `backend/tests/storage/test_sqlite_store.py::test_sessions_history_and_reports_survive_a_new_store_instance` |
| `AC-FR005-04` | A database write error is shown and leaves the visible state unchanged | `frontend/src/sessions/SessionController.test.ts::leaves the visible state unchanged when rename fails`<br>`backend/tests/api/test_threads.py::test_database_failure_is_user_safe` |
| `AC-FR013-01` | Successful generation shows progress, streams the report and stores it as current | `backend/tests/api/test_reports.py::test_generation_streams_progress_deltas_and_done`<br>`frontend/src/sessions/SessionController.test.ts::keeps the previous report until the stream completes, then replaces it`<br>`frontend/src/sessions/SessionDetail.test.tsx::disables the chat and shows progress and Cancel while generating` |
| `AC-FR013-02` | No history is rejected with a start-exploring message | `backend/tests/api/test_reports.py::test_no_history_is_rejected_before_streaming`<br>`frontend/src/sessions/SessionController.test.ts::shows the no-history message without replacing the report` |
| `AC-FR013-03` | Nothing marked relevant is rejected with a mark-at-least-one message | `backend/tests/api/test_reports.py::test_no_relevant_pair_is_rejected_in_the_analyst_language`<br>`frontend/src/sessions/SessionController.test.ts::shows the nothing-marked message without replacing the report` |
| `AC-FR013-04` | Cancelling keeps the previous report and re-enables the chat | `backend/tests/report/test_agent.py::test_cancel_keeps_the_previous_report_and_does_not_store`<br>`frontend/src/sessions/SessionController.test.ts::keeps the previous report and re-enables the chat on cancel` |
| `AC-FR013-05` | Failure shows an error and keeps the partial report flagged incomplete | `backend/tests/api/test_reports.py::test_failure_streams_a_safe_error_and_stores_the_partial_report`<br>`backend/tests/report/test_agent.py::test_failure_stores_the_partial_report_flagged_incomplete`<br>`frontend/src/sessions/SessionController.test.ts::reloads the partial report flagged incomplete when the agent fails` |
| `AC-FR013-06` | Regeneration rebuilds the report and replaces the previous one | `backend/tests/report/test_agent.py::test_regenerate_replaces_the_previous_report`<br>`frontend/src/sessions/SessionController.test.ts::keeps the previous report until the stream completes, then replaces it` |
| `AC-FR021-01` | The report plan and stored report contain plots, tables and narrative text | `backend/tests/report/test_chart_plan.py::test_validates_a_plan_and_keeps_only_answer_numbers`<br>`backend/tests/report/test_chart_plan.py::test_accepts_a_pie_and_a_table`<br>`backend/tests/report/test_openui_skill.py::test_plan_payload_keeps_plots_a_table_and_narrative`<br>`backend/tests/report/test_agent.py::test_report_stores_plots_a_table_and_narrative` |
| `AC-FR026-01` | The download is one self-contained HTML file named from the session and date and opens offline | `frontend/src/sessions/reportExport.test.ts::names the file from the session and the download date`<br>`frontend/src/sessions/reportExport.test.ts::builds a self-contained HTML with the report content and metadata`<br>`frontend/src/sessions/reportExport.test.ts::runs the real built template through the full download path`<br>`frontend/src/sessions/SessionController.test.ts::downloads the active session report with its title` |
| `AC-FR026-02` | No report downloads nothing and shows a generate-first message | `frontend/src/sessions/SessionController.test.ts::shows the no-report message and downloads nothing`<br>`frontend/src/sessions/SessionDetail.test.tsx::shows a dismissible no-report message` |
| `AC-FR028-01` | Erasing history removes that session's pairs and report only | `backend/tests/api/test_threads.py::test_erase_history_removes_pairs_and_report_of_only_that_session`<br>`frontend/src/sessions/SessionController.test.ts::erases the active session history and report after confirmation` |
| `AC-FR028-02` | Erasing the report keeps the history | `backend/tests/api/test_threads.py::test_erase_report_keeps_the_pairs_and_other_sessions`<br>`frontend/src/sessions/SessionController.test.ts::erases the report but keeps the history after confirmation` |
| `AC-FR028-03` | Deleting one pair removes only that pair and keeps the report | `backend/tests/api/test_threads.py::test_delete_one_pair_keeps_the_other_pairs_and_the_report`<br>`frontend/src/sessions/SessionController.test.ts::deletes only the confirmed pair and keeps the report` |
| `AC-FR028-04` | Declining any erase or delete confirmation changes nothing | `frontend/src/sessions/SessionController.test.ts::does nothing when deletion is declined`<br>`frontend/src/sessions/SessionController.test.ts::does nothing when erasing history is declined`<br>`frontend/src/sessions/SessionController.test.ts::does nothing when erasing the report is declined` |
| `AC-FR028-05` | With no history and no report, both erase buttons are disabled | `frontend/src/sessions/SessionDetail.test.tsx::disables both erase actions when there is no history and no report` |
| `AC-FR035-01` | Answer, report and error language follows the analyst | `backend/tests/connector/test_language.py::test_instructions_follow_the_language`<br>`backend/tests/connector/test_language.py::test_error_messages_are_localized_and_generic`<br>`backend/tests/connector/test_openui.py::test_spanish_conversion_instruction_is_passed`<br>`backend/tests/report/test_chart_plan.py::test_skill_writes_spanish_instructions`<br>`backend/tests/report/test_openui_skill.py::test_spanish_report_instruction_is_passed`<br>`backend/tests/api/test_reports.py::test_no_relevant_pair_is_rejected_in_the_analyst_language`<br>`frontend/src/sessions/chatClient.test.ts::shows the localized backend error` |

## Manual checklist

Run this after the automated gates pass. It takes about 10 minutes. Use only synthetic or trusted local data; do not put secrets, graph content or question text in the checklist or in any tracked file.

1. Start the backend and frontend as described in the README, then open <http://localhost:5173>.
2. Create a session, rename it, create a second session, switch between them, then delete one and confirm the list updates.
3. Ask two questions in the chat. Check that each answer appears as readable text and that its chart is available behind **Show chart**.
4. Switch the relevance toggle off for one answer, select the other session and come back; check the toggle stays off.
5. Delete one question-answer pair with confirmation; check that only that pair disappears.
6. Press **Generate Report**, check that the chat is disabled and progress is shown, then press **Cancel**. Check that any previous report is still there and the chat is enabled.
7. Press **Generate Report** again and wait; check that the new report replaces the previous one and contains narrative, charts and tables.
8. Press **Download Report**, open the downloaded HTML file offline, and check its narrative, charts, tables and styling.
9. Restart the backend and frontend, select the session again, and check that its history and report are still there.
10. Press **Erase Report**, confirm, and check that the report is gone while the history remains. Then press **Erase History**, confirm, and check that both are gone.
11. Switch the theme control between **System**, **Light** and **Dark**. Check that the chat, report, charts, tables and labels stay readable in both modes.

The manual checklist is pending the project owner's run. TASK-033 remains deferred until the final knowledge graph and final curated question set exist.
