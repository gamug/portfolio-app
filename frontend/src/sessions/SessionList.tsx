import { useState } from "react";
import type { SessionState } from "./SessionController";

type SessionListProps = {
  state: SessionState;
  onCreate: () => void;
  onSelect: (sessionId: string) => void;
  onRename: (sessionId: string, title: string) => void;
  onDelete: (sessionId: string) => void;
  onDismissError: () => void;
};

export function SessionList({
  state,
  onCreate,
  onSelect,
  onRename,
  onDelete,
  onDismissError,
}: SessionListProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftTitle, setDraftTitle] = useState("");
  const [confirmingId, setConfirmingId] = useState<string | null>(null);

  const startRename = (sessionId: string, title: string) => {
    setEditingId(sessionId);
    setDraftTitle(title);
    setConfirmingId(null);
  };

  const saveRename = () => {
    if (editingId === null || draftTitle.trim().length === 0) {
      return;
    }
    onRename(editingId, draftTitle);
    setEditingId(null);
  };

  return (
    <aside className="session-list" aria-label="Sessions">
      <div className="session-list__header">
        <h1>Sessions</h1>
        <button type="button" onClick={onCreate} disabled={state.isLoading}>
          New session
        </button>
      </div>

      {state.error !== null && (
        <div className="session-list__error" role="alert">
          <span>{state.error}</span>
          <button type="button" onClick={onDismissError} aria-label="Dismiss error">
            ×
          </button>
        </div>
      )}

      {state.sessions.length === 0 ? (
        <p className="session-list__empty">No sessions yet.</p>
      ) : (
        <ul>
          {state.sessions.map((session) => (
            <li
              key={session.id}
              className={session.id === state.activeSessionId ? "is-active" : undefined}
            >
              {editingId === session.id ? (
                <form
                  className="session-list__rename"
                  onSubmit={(event) => {
                    event.preventDefault();
                    saveRename();
                  }}
                >
                  <input
                    value={draftTitle}
                    onChange={(event) => setDraftTitle(event.target.value)}
                    aria-label="Session name"
                    autoFocus
                  />
                  <button type="submit">Save</button>
                  <button type="button" onClick={() => setEditingId(null)}>
                    Cancel
                  </button>
                </form>
              ) : (
                <div className="session-list__row">
                  <button
                    type="button"
                    className="session-list__select"
                    title={session.title}
                    onClick={() => onSelect(session.id)}
                  >
                    {session.title}
                  </button>
                  <div className="session-list__actions">
                    <button
                      type="button"
                      onClick={() => startRename(session.id, session.title)}
                      aria-label={`Rename ${session.title}`}
                    >
                      Rename
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setConfirmingId(session.id);
                        setEditingId(null);
                      }}
                      aria-label={`Delete ${session.title}`}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              )}

              {confirmingId === session.id && (
                <div className="session-list__confirm" role="alertdialog">
                  <span>Delete this session and its history?</span>
                  <button
                    type="button"
                    onClick={() => {
                      setConfirmingId(null);
                      onDelete(session.id);
                    }}
                  >
                    Delete
                  </button>
                  <button type="button" onClick={() => setConfirmingId(null)}>
                    Cancel
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}
