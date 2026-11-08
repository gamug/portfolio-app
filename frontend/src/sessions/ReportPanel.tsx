import { Renderer } from "@openuidev/react-lang";
import { openuiLibrary } from "@openuidev/react-ui/genui-lib";
import type { SessionState } from "./SessionController";

type ReportPanelProps = {
  state: SessionState;
  onGenerate: () => void;
  onDownload: () => void;
  onCancel: () => void;
};

const PROGRESS_LABELS = {
  planning: "Planning the report…",
  rendering: "Rendering the report…",
} as const;

export function ReportPanel({ state, onGenerate, onDownload, onCancel }: ReportPanelProps) {
  const controlsDisabled = state.isLoading || state.isGeneratingReport || state.isSendingChat;
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
          <button type="button" onClick={onGenerate} disabled={controlsDisabled}>
            {state.report === null ? "Generate Report" : "Regenerate Report"}
          </button>
          {state.report !== null && (
            <button type="button" onClick={onDownload} disabled={controlsDisabled}>
              Download Report
            </button>
          )}
          {state.isGeneratingReport && (
            <button type="button" onClick={onCancel}>
              Cancel
            </button>
          )}
        </div>
      </div>

      {state.isGeneratingReport && (
        <p className="report-panel__progress" role="status">
          {progress}
        </p>
      )}
      {state.reportError !== null && (
        <div className="panel-error" role="alert">
          {state.reportError}
        </div>
      )}

      <div className="report-panel__body" data-report-view={view}>
        {view === "stream" ? (
          <Renderer response={state.reportStream} library={openuiLibrary} />
        ) : view === "current" && state.report !== null ? (
          <Renderer response={state.report.openui_lang} library={openuiLibrary} />
        ) : (
          <p>No report yet.</p>
        )}
      </div>
    </section>
  );
}
