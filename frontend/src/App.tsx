import { useEffect, useMemo } from "react";
import { restStorage } from "@openuidev/react-ui";
import { SessionController } from "./sessions/SessionController";
import { SessionDetail } from "./sessions/SessionDetail";
import { SessionList } from "./sessions/SessionList";
import { createReportClient } from "./sessions/reportClient";
import { useSessionController } from "./sessions/useSessionController";

export function App() {
  const storage = useMemo(() => restStorage({ baseUrl: "/api/threads" }), []);
  const controller = useMemo(
    () => new SessionController(storage.thread, createReportClient("/api/threads")),
    [storage],
  );
  const state = useSessionController(controller);

  useEffect(() => {
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
      <SessionDetail state={state} />
    </div>
  );
}
