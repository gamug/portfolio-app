import { useEffect, useMemo, useRef } from "react";
import { restStorage } from "@openuidev/react-ui";
import { SessionController } from "./sessions/SessionController";
import { SessionDetail } from "./sessions/SessionDetail";
import { SessionList } from "./sessions/SessionList";
import { createChatClient } from "./sessions/chatClient";
import { createPairClient } from "./sessions/pairClient";
import { createRelevanceClient } from "./sessions/relevanceClient";
import { createReportClient } from "./sessions/reportClient";
import { createReportExporter } from "./sessions/reportExport";
import { useSessionController } from "./sessions/useSessionController";

export function App() {
  const storage = useMemo(() => restStorage({ baseUrl: "/api/threads" }), []);
  const controller = useMemo(
    () =>
      new SessionController(
        storage.thread,
        createReportClient("/api/threads"),
        createRelevanceClient("/api/threads"),
        createPairClient("/api/threads"),
        createChatClient("/api"),
        createReportExporter(),
      ),
    [storage],
  );
  const state = useSessionController(controller);
  const initialized = useRef(false);

  useEffect(() => {
    if (initialized.current) {
      return;
    }
    initialized.current = true;
    void controller.initialize();
  }, [controller]);

  return (
    <div className="app-shell">
      <SessionList
        state={state}
        onCreate={() => void controller.createSession()}
        onSelect={(sessionId) => void controller.selectSession(sessionId)}
        onRename={(sessionId, title) => void controller.renameSession(sessionId, title)}
        onDelete={(sessionId) => void controller.deleteSession(sessionId, true)}
        onDismissError={() => controller.dismissError()}
      />
      <SessionDetail
        state={state}
        onToggleRelevance={(pairId) => void controller.toggleRelevance(pairId)}
        onDeletePair={(pairId) => void controller.deletePair(pairId, true)}
        onSendQuestion={(question) => void controller.sendQuestion(question)}
        onGenerateReport={() => void controller.generateReport()}
        onDownloadReport={() => void controller.downloadReport()}
        onDismissDownloadNotice={() => controller.dismissDownloadNotice()}
        onCancelReport={() => controller.cancelReportGeneration()}
      />
    </div>
  );
}
