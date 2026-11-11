import { useReducer, useState } from "react";
import { Renderer } from "@openuidev/react-lang";
import type { Message } from "@openuidev/react-ui";
import { portfolioChatLibrary } from "../openui/portfolioLibrary";
import { AnswerText } from "./AnswerText";
import { extractAnswerText, messageText } from "./answerText";
import type { SessionState } from "./SessionController";

type PairAnswerProps = {
  message: Message;
  state: SessionState;
  onToggleRelevance: (pairId: string) => void;
  onDeletePair: (pairId: string) => void;
  initialShowChart?: boolean;
};

export function chartReducer(open: boolean): boolean {
  return !open;
}

export function PairAnswer({
  message,
  state,
  onToggleRelevance,
  onDeletePair,
  initialShowChart = false,
}: PairAnswerProps) {
  const [showChart, toggleChart] = useReducer(chartReducer, initialShowChart);
  const [confirming, setConfirming] = useState(false);
  const controlsDisabled = state.isLoading || state.isGeneratingReport || state.isSendingChat;
  const rawContent = messageText(message);
  const answerText = extractAnswerText(rawContent);

  return (
    <>
      {answerText.length > 0 ? (
        <AnswerText text={answerText} />
      ) : (
        <p className="answer-text answer-text--empty">
          The stored answer has no separate text summary.
        </p>
      )}

      <button
        type="button"
        className="message__chart-toggle"
        aria-expanded={showChart}
        onClick={() => toggleChart()}
      >
        {showChart ? "Hide chart" : "Show chart"}
      </button>

      {showChart && (
        <div className="message__chart" data-chart-view="open">
          <Renderer response={rawContent} library={portfolioChatLibrary} />
        </div>
      )}

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

      {confirming ? (
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
      ) : (
        <button
          type="button"
          data-delete-pair-id={message.id}
          disabled={controlsDisabled}
          onClick={() => setConfirming(true)}
        >
          Delete pair
        </button>
      )}
    </>
  );
}
