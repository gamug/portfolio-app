import { useState } from "react";
import { Renderer } from "@openuidev/react-lang";
import { portfolioReportLibrary } from "../openui/portfolioLibrary";
import type { SessionState } from "./SessionController";

type ReportPanelProps = {
  state: SessionState;
  onGenerate: () => void;
  onDownload: () => void;
  onDismissDownloadNotice: () => void;
  onEraseHistory: () => void;
  onEraseReport: () => void;
  onCancel: () => void;
};

type EraseTarget = "history" | "report";

const PROGRESS_LABELS = {
  planning: "Planning the report…",
  rendering: "Rendering the report…",
} as const;

export function ReportPanel({
  state,
  onGenerate,
  onDownload,
  onDismissDownloadNotice,
  onEraseHistory,
  onEraseReport,
  onCancel,
}: ReportPanelProps) {
  const [confirmingErase, setConfirmingErase] = useState<EraseTarget | null>(null);
  const controlsDisabled = state.isLoading || state.isGeneratingReport || state.isSendingChat;
  const downloadDisabled =
    state.isLoading || (state.report !== null && (state.isGeneratingReport || state.isSendingChat));
  const historyEraseDisabled =
    controlsDisabled || (state.messages.length === 0 && state.report === null);
  const reportEraseDisabled = controlsDisabled || state.report === null;
  const progress =
    state.reportProgress === null
      ? PROGRESS_LABELS.planning
      : PROGRESS_LABELS[state.reportProgress];
  const view =
    state.reportStream.length > 0 ? "stream" : state.report === null ? "empty" : "current";

  return (
    <section className="report-panel" aria-label="Report">
      <div className="panel-header">
        <h3>
          Report{" "}
          {state.report?.incomplete === true && (
            <span className="report-panel__incomplete">(incomplete)</span>
          )}
        </h3>
        <div className="report-panel__actions">
          <button
            type="button"
            className="report-panel__action report-panel__action--primary"
            onClick={onGenerate}
            disabled={controlsDisabled}
          >
            {state.report === null ? "Generate Report" : "Regenerate Report"}
          </button>
          <button
            type="button"
            className="report-panel__action report-panel__action--secondary"
            onClick={onDownload}
            disabled={downloadDisabled}
          >
            Download Report
          </button>
          {state.isGeneratingReport && (
            <button
              type="button"
              className="report-panel__action report-panel__action--cancel"
              onClick={onCancel}
            >
              Cancel
            </button>
          )}
          <span className="report-panel__actions-divider" aria-hidden="true" />
          <button
            type="button"
            className="report-panel__action report-panel__action--danger"
            onClick={() => setConfirmingErase("history")}
            disabled={historyEraseDisabled}
          >
            Erase History
          </button>
          <button
            type="button"
            className="report-panel__action report-panel__action--danger"
            onClick={() => setConfirmingErase("report")}
            disabled={reportEraseDisabled}
          >
            Erase Report
          </button>
        </div>
      </div>

      {confirmingErase === "history" && (
        <div className="panel-confirm" role="alertdialog">
          <span>Erase all history and the report of this session?</span>
          <button
            type="button"
            disabled={controlsDisabled}
            onClick={() => {
              setConfirmingErase(null);
              onEraseHistory();
            }}
          >
            Erase
          </button>
          <button type="button" onClick={() => setConfirmingErase(null)}>
            Cancel
          </button>
        </div>
      )}
      {confirmingErase === "report" && (
        <div className="panel-confirm" role="alertdialog">
          <span>Erase the report of this session? The history is kept.</span>
          <button
            type="button"
            disabled={controlsDisabled}
            onClick={() => {
              setConfirmingErase(null);
              onEraseReport();
            }}
          >
            Erase
          </button>
          <button type="button" onClick={() => setConfirmingErase(null)}>
            Cancel
          </button>
        </div>
      )}

      {state.isGeneratingReport && (
        <p className="report-panel__progress status-pill" role="status">
          {progress}
        </p>
      )}
      {state.reportError !== null && (
        <div className="panel-error" role="alert">
          {state.reportError}
        </div>
      )}
      {state.report === null && state.downloadNotice !== null && (
        <div className="panel-notice" role="status">
          <span>{state.downloadNotice}</span>
          <button type="button" onClick={onDismissDownloadNotice} aria-label="Dismiss message">
            ×
          </button>
        </div>
      )}

      <div className="report-panel__body" data-report-view={view}>
        {view === "stream" ? (
          <Renderer response={state.reportStream} library={portfolioReportLibrary} />
        ) : view === "current" && state.report !== null ? (
          <Renderer response={state.report.openui_lang} library={portfolioReportLibrary} />
        ) : (
          <div className="empty-state empty-state--report">
            <p>No report yet.</p>
          </div>
        )}
      </div>
    </section>
  );
}
