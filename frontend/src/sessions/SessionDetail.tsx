import { ThemeToggle } from "../ThemeToggle";
import { ChatPanel } from "./ChatPanel";
import { ReportPanel } from "./ReportPanel";
import type { SessionState } from "./SessionController";

type SessionDetailProps = {
  state: SessionState;
  onToggleRelevance: (pairId: string) => void;
  onDeletePair: (pairId: string) => void;
  onSendQuestion: (question: string) => void;
  onGenerateReport: () => void;
  onCancelReport: () => void;
};

export function SessionDetail({
  state,
  onToggleRelevance,
  onDeletePair,
  onSendQuestion,
  onGenerateReport,
  onCancelReport,
}: SessionDetailProps) {
  const active = state.sessions.find((session) => session.id === state.activeSessionId);
  if (active === undefined) {
    return (
      <main className="session-detail session-detail--empty">
        <p>Create a session to start exploring the knowledge graph.</p>
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
          key={state.activeSessionId ?? "none"}
          state={state}
          onToggleRelevance={onToggleRelevance}
          onDeletePair={onDeletePair}
          onSendQuestion={onSendQuestion}
        />
        <ReportPanel state={state} onGenerate={onGenerateReport} onCancel={onCancelReport} />
      </div>
    </main>
  );
}
