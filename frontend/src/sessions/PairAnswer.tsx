import { useEffect, useReducer, useRef, useState } from "react";
import { Renderer } from "@openuidev/react-lang";
import type { Message } from "@openuidev/react-ui";
import { portfolioChatLibrary } from "../openui/portfolioLibrary";
import { AnswerText } from "./AnswerText";
import { extractAnswerText, messageText } from "./answerText";
import type { SessionState } from "./SessionController";
import type { SparqlClient } from "./sparqlClient";

type PairAnswerProps = {
  message: Message;
  state: SessionState;
  onToggleRelevance: (pairId: string) => void;
  onDeletePair: (pairId: string) => void;
  initialShowChart?: boolean;
  loadSparql?: SparqlClient["getSparql"];
};

export function chartReducer(open: boolean): boolean {
  return !open;
}

export type SparqlState = {
  open: boolean;
  queries: string[] | null;
  loading: boolean;
  error: string | null;
};

export type SparqlAction =
  | { type: "toggle" }
  | { type: "loading" }
  | { type: "loaded"; queries: string[] }
  | { type: "failed"; error: string }
  | { type: "reset" };

export const INITIAL_SPARQL_STATE: SparqlState = {
  open: false,
  queries: null,
  loading: false,
  error: null,
};

export const SPARQL_ERROR = "Could not load the SPARQL query. Please try again.";

export function sparqlReducer(state: SparqlState, action: SparqlAction): SparqlState {
  switch (action.type) {
    case "toggle":
      return { ...state, open: !state.open };
    case "loading":
      return { ...state, loading: true, error: null };
    case "loaded":
      return { ...state, loading: false, queries: action.queries, error: null };
    case "failed":
      return { ...state, loading: false, error: action.error };
    case "reset":
      return INITIAL_SPARQL_STATE;
  }
}

export function needsSparqlFetch(state: SparqlState): boolean {
  return state.open && state.queries === null && !state.loading;
}

type SparqlQueriesPanelProps = {
  state: SparqlState;
  copiedIndex: number | null;
  onCopy: (query: string, index: number) => void;
};

export function SparqlQueriesPanel({ state, copiedIndex, onCopy }: SparqlQueriesPanelProps) {
  if (!state.open) {
    return null;
  }

  return (
    <article className="message__card">
      {state.loading && (
        <p className="message__sparql-status" role="status">
          Loading SPARQL query…
        </p>
      )}
      {state.error !== null && (
        <p className="message__sparql-status message__sparql-status--error" role="alert">
          {state.error}
        </p>
      )}
      {!state.loading &&
        state.error === null &&
        state.queries !== null &&
        state.queries.length === 0 && (
          <p className="message__sparql-status">No SPARQL query recorded for this answer.</p>
        )}
      {!state.loading &&
        state.error === null &&
        state.queries !== null &&
        state.queries.map((query, index) => (
          <div className="message__sparql" key={`${index}-${query.slice(0, 24)}`}>
            <div className="message__sparql-header">
              <span className="message__sparql-title">
                {state.queries !== null && state.queries.length > 1
                  ? `SPARQL query ${index + 1}`
                  : "SPARQL query"}
              </span>
              <button
                type="button"
                className="message__sparql-copy"
                onClick={() => onCopy(query, index)}
              >
                {copiedIndex === index ? "Copied" : "Copy"}
              </button>
            </div>
            <pre>
              <code>{query}</code>
            </pre>
          </div>
        ))}
    </article>
  );
}

export function PairAnswer({
  message,
  state,
  onToggleRelevance,
  onDeletePair,
  initialShowChart = false,
  loadSparql,
}: PairAnswerProps) {
  const [showChart, toggleChart] = useReducer(chartReducer, initialShowChart);
  const [confirming, setConfirming] = useState(false);
  const [sparql, dispatchSparql] = useReducer(sparqlReducer, INITIAL_SPARQL_STATE);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const sparqlRequest = useRef(0);
  const controlsDisabled = state.isLoading || state.isGeneratingReport || state.isSendingChat;
  const rawContent = messageText(message);
  const answerText = extractAnswerText(rawContent);

  useEffect(() => {
    sparqlRequest.current += 1;
    dispatchSparql({ type: "reset" });
    setCopiedIndex(null);
  }, [message.id]);

  useEffect(() => {
    if (copiedIndex === null) {
      return;
    }
    const timer = window.setTimeout(() => setCopiedIndex(null), 1500);
    return () => window.clearTimeout(timer);
  }, [copiedIndex]);

  async function toggleSparql(): Promise<void> {
    const next = sparqlReducer(sparql, { type: "toggle" });
    dispatchSparql({ type: "toggle" });
    if (!needsSparqlFetch(next)) {
      return;
    }
    if (loadSparql === undefined || state.activeSessionId === null) {
      dispatchSparql({ type: "failed", error: SPARQL_ERROR });
      return;
    }
    dispatchSparql({ type: "loading" });
    const request = sparqlRequest.current;
    try {
      const queries = await loadSparql(state.activeSessionId, message.id);
      if (sparqlRequest.current === request) {
        dispatchSparql({ type: "loaded", queries });
      }
    } catch {
      if (sparqlRequest.current === request) {
        dispatchSparql({ type: "failed", error: SPARQL_ERROR });
      }
    }
  }

  async function copyQuery(query: string, index: number): Promise<void> {
    try {
      await navigator.clipboard.writeText(query);
      setCopiedIndex(index);
    } catch {
      // Keep the Copy label when the clipboard API is unavailable or denied.
    }
  }

  return (
    <>
      {answerText.length > 0 ? (
        <AnswerText text={answerText} />
      ) : (
        <p className="answer-text answer-text--empty">
          The stored answer has no separate text summary.
        </p>
      )}

      {showChart && (
        <div className="message__chart" data-chart-view="open">
          <Renderer response={rawContent} library={portfolioChatLibrary} />
        </div>
      )}

      <SparqlQueriesPanel
        state={sparql}
        copiedIndex={copiedIndex}
        onCopy={(query, index) => void copyQuery(query, index)}
      />

      <div className="message__footer">
        <div className="message__footer-left">
          <button
            type="button"
            className="message__chart-toggle"
            aria-expanded={showChart}
            onClick={() => toggleChart()}
          >
            {showChart ? "Hide chart" : "Show chart"}
          </button>

          <button
            type="button"
            className="message__sparql-toggle"
            aria-expanded={sparql.open}
            onClick={() => void toggleSparql()}
          >
            {sparql.open ? "Hide SPARQL query" : "Show SPARQL query"}
          </button>

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
        </div>

        {!confirming && (
          <button
            type="button"
            data-delete-pair-id={message.id}
            disabled={controlsDisabled}
            onClick={() => setConfirming(true)}
          >
            Delete pair
          </button>
        )}
      </div>

      {confirming && (
        <div className="message__confirm" role="alertdialog">
          <span>Delete this question-answer pair?</span>
          <button
            type="button"
            disabled={controlsDisabled}
            onClick={() => {
              setConfirming(false);
              onDeletePair(message.id);
            }}
          >
            Delete
          </button>
          <button type="button" onClick={() => setConfirming(false)}>
            Cancel
          </button>
        </div>
      )}
    </>
  );
}
