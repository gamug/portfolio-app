import { useState, type FormEvent } from "react";
import { Renderer } from "@openuidev/react-lang";
import type { Message } from "@openuidev/react-ui";
import { openuiChatLibrary } from "@openuidev/react-ui/genui-lib";
import type { SessionState } from "./SessionController";

type ChatPanelProps = {
  state: SessionState;
  onToggleRelevance: (pairId: string) => void;
  onDeletePair: (pairId: string) => void;
  onSendQuestion: (question: string) => void;
};

function messageText(message: Message): string {
  return typeof message.content === "string" ? message.content : "";
}

export function ChatPanel({
  state,
  onToggleRelevance,
  onDeletePair,
  onSendQuestion,
}: ChatPanelProps) {
  const [draft, setDraft] = useState("");
  const [confirmingPairId, setConfirmingPairId] = useState<string | null>(null);
  const controlsDisabled = state.isLoading || state.isGeneratingReport || state.isSendingChat;
  const canSend = !controlsDisabled && draft.trim().length > 0;

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const question = draft.trim();
    if (question.length === 0 || controlsDisabled) {
      return;
    }
    onSendQuestion(question);
    setDraft("");
  };

  return (
    <section className="chat-panel" aria-label="Chat">
      <div className="panel-header">
        <h3>Chat</h3>
        {state.isSendingChat && <span role="status">Waiting for the answer…</span>}
      </div>

      {state.isGeneratingReport && (
        <p className="chat-panel__notice">Report generation in progress; the chat is disabled.</p>
      )}
      {state.chatError !== null && (
        <div className="panel-error" role="alert">
          {state.chatError}
        </div>
      )}

      <div className="chat-panel__history">
        <h4>History</h4>
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
                          disabled={controlsDisabled}
                          onChange={() => onToggleRelevance(message.id)}
                        />
                        Relevant for report
                      </label>
                    </div>
                    {confirmingPairId === message.id ? (
                      <div className="message__confirm" role="alertdialog">
                        <span>Delete this question-answer pair?</span>
                        <button
                          type="button"
                          onClick={() => {
                            setConfirmingPairId(null);
                            onDeletePair(message.id);
                          }}
                        >
                          Delete
                        </button>
                        <button type="button" onClick={() => setConfirmingPairId(null)}>
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <button
                        type="button"
                        data-delete-pair-id={message.id}
                        disabled={controlsDisabled}
                        onClick={() => setConfirmingPairId(message.id)}
                      >
                        Delete pair
                      </button>
                    )}
                  </>
                ) : (
                  <p>{messageText(message)}</p>
                )}
              </li>
            ))}
          </ol>
        )}
      </div>

      {state.chatStream !== null && (
        <div className="chat-panel__stream" aria-live="polite">
          <div className="message message--user">
            <p>{state.chatStream.question}</p>
          </div>
          <div className="message message--assistant">
            {state.chatStream.answer.length > 0 ? (
              <p className="chat-panel__raw">{state.chatStream.answer}</p>
            ) : (
              <p>Waiting for the answer…</p>
            )}
          </div>
        </div>
      )}

      <form className="chat-panel__composer" onSubmit={submit}>
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Ask the knowledge graph"
          aria-label="Question"
          disabled={controlsDisabled}
        />
        <button type="submit" disabled={!canSend}>
          Send
        </button>
      </form>
    </section>
  );
}
