import { Renderer } from "@openuidev/react-lang";
import type { Message } from "@openuidev/react-ui";
import { openuiChatLibrary, openuiLibrary } from "@openuidev/react-ui/genui-lib";
import type { SessionState } from "./SessionController";

type SessionDetailProps = {
  state: SessionState;
  onToggleRelevance: (pairId: string) => void;
};

function messageText(message: Message): string {
  return typeof message.content === "string" ? message.content : "";
}

export function SessionDetail({ state, onToggleRelevance }: SessionDetailProps) {
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
      </header>

      <section className="session-detail__history" aria-label="History">
        <h3>History</h3>
        {state.messages.length === 0 ? (
          <p>No questions yet in this session.</p>
        ) : (
          <ol>
            {state.messages.map((message) => (
              <li key={message.id} className={`message message--${message.role}`}>
                {message.role === "assistant" ? (
                  <>
                    <Renderer response={messageText(message)} library={openuiChatLibrary} />
                    <div className="message__relevance">
                      <label>
                        <input
                          type="checkbox"
                          data-pair-id={message.id}
                          checked={state.relevance[message.id] ?? true}
                          disabled={state.isLoading}
                          onChange={() => onToggleRelevance(message.id)}
                        />
                        Relevant for report
                      </label>
                    </div>
                  </>
                ) : (
                  <p>{messageText(message)}</p>
                )}
              </li>
            ))}
          </ol>
        )}
      </section>

      <section className="session-detail__report" aria-label="Report">
        <h3>Report {state.report?.incomplete === true && <span>(incomplete)</span>}</h3>
        {state.report === null ? (
          <p>No report yet.</p>
        ) : (
          <Renderer response={state.report.openui_lang} library={openuiLibrary} />
        )}
      </section>
    </main>
  );
}
