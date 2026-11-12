import { ThemeToggle } from "../ThemeToggle";
import { ChatPanel } from "./ChatPanel";
import { ReportPanel } from "./ReportPanel";
import type { SessionState } from "./SessionController";
import type { SparqlClient } from "./sparqlClient";

type SessionDetailProps = {
  state: SessionState;
  onToggleRelevance: (pairId: string) => void;
  onDeletePair: (pairId: string) => void;
  onSendQuestion: (question: string) => void;
  onGenerateReport: () => void;
  onDownloadReport: () => void;
  onDismissDownloadNotice: () => void;
  onEraseHistory: () => void;
  onEraseReport: () => void;
  onCancelReport: () => void;
  loadSparql?: SparqlClient["getSparql"];
};

export function SessionDetail({
  state,
  onToggleRelevance,
  onDeletePair,
  onSendQuestion,
  onGenerateReport,
  onDownloadReport,
  onDismissDownloadNotice,
  onEraseHistory,
  onEraseReport,
  onCancelReport,
  loadSparql,
}: SessionDetailProps) {
  const active = state.sessions.find((session) => session.id === state.activeSessionId);
  if (active === undefined) {
    return (
      <main className="session-detail session-detail--empty">
        <div className="empty-state empty-state--session">
          <p>Create a session to start exploring the knowledge graph.</p>
        </div>
      </main>
    );
  }

  return (
    <main className="session-detail">
      <header>
        <h2>{active.title}</h2>
        {state.isLoading && <span role="status">Loading…</span>}
        <ThemeToggle />
      </header>

      <div className="session-detail__panels">
        <ChatPanel
          key={`chat-${state.activeSessionId ?? "none"}`}
          state={state}
          onToggleRelevance={onToggleRelevance}
          onDeletePair={onDeletePair}
          onSendQuestion={onSendQuestion}
          loadSparql={loadSparql}
        />
        <ReportPanel
          key={`report-${state.activeSessionId ?? "none"}`}
          state={state}
          onGenerate={onGenerateReport}
          onDownload={onDownloadReport}
          onDismissDownloadNotice={onDismissDownloadNotice}
          onEraseHistory={onEraseHistory}
          onEraseReport={onEraseReport}
          onCancel={onCancelReport}
        />
      </div>
    </main>
  );
}
