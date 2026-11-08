import { Children, isValidElement, type ReactElement, type ReactNode } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { ChatPanel } from "./ChatPanel";
import { ReportPanel } from "./ReportPanel";
import { SessionDetail } from "./SessionDetail";
import { NO_REPORT_MESSAGE, type SessionState } from "./SessionController";

const baseState: SessionState = {
  sessions: [{ id: "s1", title: "Session", createdAt: "2026-11-07T00:00:00Z" }],
  activeSessionId: "s1",
  messages: [{ id: "p1", role: "assistant", content: "root = Card([])" }],
  report: null,
  relevance: { p1: false },
  isLoading: false,
  error: null,
  isSendingChat: false,
  chatStream: null,
  chatError: null,
  isGeneratingReport: false,
  reportProgress: null,
  reportStream: "",
  reportError: null,
  downloadNotice: null,
};

const noopHandlers = {
  onToggleRelevance: () => undefined,
  onDeletePair: () => undefined,
  onSendQuestion: () => undefined,
  onGenerateReport: () => undefined,
  onDownloadReport: () => undefined,
  onDismissDownloadNotice: () => undefined,
  onEraseHistory: () => undefined,
  onEraseReport: () => undefined,
  onCancelReport: () => undefined,
};

function renderDetailElement(state: SessionState) {
  return <SessionDetail state={state} {...noopHandlers} />;
}

function renderDetail(overrides: Partial<SessionState> = {}): string {
  return renderToStaticMarkup(renderDetailElement({ ...baseState, ...overrides }));
}

function panelElements(state: SessionState): ReactElement[] {
  const detail = SessionDetail({ state, ...noopHandlers });
  const panelsContainer = Children.toArray(detail.props.children).find(
    (child): child is ReactElement<{ children: ReactNode }> =>
      isValidElement(child) && child.type === "div",
  );
  if (panelsContainer === undefined) {
    throw new Error("SessionDetail did not render the panels container");
  }
  return Children.toArray(panelsContainer.props.children).filter(isValidElement);
}

describe("SessionDetail chat and report panels", () => {
  it("renders the chat and report panels side by side with the input and actions", () => {
    const html = renderDetail();
    expect(html).toContain('aria-label="Chat"');
    expect(html).toContain('aria-label="Report"');
    expect(html).toContain('aria-label="Question"');
    expect(html).toContain("Send");
    expect(html).toContain("Generate Report");
    expect(html).toContain("Download Report");
    expect(html).toContain("Erase History");
    expect(html).toContain("Erase Report");
    expect(html).toMatch(/disabled=""[^>]*>Erase Report/);
    expect(html).not.toMatch(/disabled=""[^>]*>Erase History/);
    expect(html).toContain("No report yet.");
    expect(html).toContain('data-report-view="empty"');
  });

  it("keeps one chat and one report panel across session switches", () => {
    const sessions = [
      { id: "s1", title: "One", createdAt: "2026-11-07T00:00:00Z" },
      { id: "s2", title: "Two", createdAt: "2026-11-07T00:00:00Z" },
      { id: "s3", title: "Three", createdAt: "2026-11-07T00:00:00Z" },
    ];

    for (const activeSessionId of ["s1", "s2", "s3"]) {
      const state = { ...baseState, sessions, activeSessionId };
      const html = renderToStaticMarkup(renderDetailElement(state));
      expect(html.match(/aria-label="Chat"/g) ?? []).toHaveLength(1);
      expect(html.match(/aria-label="Report"/g) ?? []).toHaveLength(1);

      const [chat, report] = panelElements(state);
      expect(chat.type).toBe(ChatPanel);
      expect(report.type).toBe(ReportPanel);
      const chatKey = String(chat.key);
      const reportKey = String(report.key);
      expect(chatKey).toContain(`chat-${activeSessionId}`);
      expect(reportKey).toContain(`report-${activeSessionId}`);
      expect(chatKey).not.toBe(reportKey);
    }
  });

  it("disables both erase actions when there is no history and no report", () => {
    const html = renderDetail({ messages: [], relevance: {} });
    expect(html).toMatch(/disabled=""[^>]*>Erase History/);
    expect(html).toMatch(/disabled=""[^>]*>Erase Report/);
  });

  it("shows a dismissible no-report message", () => {
    const html = renderDetail({ downloadNotice: NO_REPORT_MESSAGE });
    expect(html).toContain(NO_REPORT_MESSAGE);
    expect(html).toContain('aria-label="Dismiss message"');
    expect(html).toContain("Download Report");
  });

  it("hides the no-report message when a report exists", () => {
    const html = renderDetail({
      downloadNotice: NO_REPORT_MESSAGE,
      report: {
        openui_lang: "root = Card([])",
        incomplete: false,
        created_at: "2026-11-07T00:00:00Z",
        updated_at: "2026-11-07T00:00:00Z",
      },
    });
    expect(html).not.toContain(NO_REPORT_MESSAGE);
    expect(html).toContain("Download Report");
  });

  it("renders one relevance toggle per answer with its stored state", () => {
    const html = renderDetail();
    expect(html).toContain('data-pair-id="p1"');
    expect(html).toContain("Relevant for report");
    expect(html).toContain('data-delete-pair-id="p1"');
    expect(html).not.toContain('data-pair-id="p1" checked=""');
  });

  it("disables the chat and shows progress and Cancel while generating", () => {
    const html = renderDetail({
      isGeneratingReport: true,
      reportProgress: "rendering",
      reportStream: "root = Card([])",
    });
    expect(html).toContain("Rendering the report…");
    expect(html).toContain("Cancel");
    expect(html).toContain("Report generation in progress; the chat is disabled.");
    expect(html).toMatch(/aria-label="Question"[^>]*disabled/);
    expect(html).toMatch(/disabled=""[^>]*>Send/);
    expect(html).toContain("Download Report");
    expect(html).not.toMatch(/disabled=""[^>]*>Download Report/);
    expect(html).toMatch(/disabled=""[^>]*>Erase History/);
    expect(html).toMatch(/disabled=""[^>]*>Erase Report/);
    expect(html).toContain('data-report-view="stream"');
  });

  it("shows a partial report as incomplete with an error after failure", () => {
    const html = renderDetail({
      report: {
        openui_lang: "root = Card([])",
        incomplete: true,
        created_at: "2026-11-07T00:00:00Z",
        updated_at: "2026-11-07T00:00:00Z",
      },
      reportError: "The report could not be generated.",
    });
    expect(html).toContain("(incomplete)");
    expect(html).toContain("The report could not be generated.");
    expect(html).toContain("Regenerate Report");
    expect(html).toContain("Download Report");
    expect(html).not.toMatch(/disabled=""[^>]*>Erase History/);
    expect(html).not.toMatch(/disabled=""[^>]*>Erase Report/);
    expect(html).toContain('data-report-view="current"');
  });

  it("shows the chat error and the streamed raw answer", () => {
    const html = renderDetail({
      chatError: "No se pudo generar la respuesta.",
      chatStream: { question: "¿Pregunta?", answer: "Respuesta parcial" },
    });
    expect(html).toContain("No se pudo generar la respuesta.");
    expect(html).toContain("¿Pregunta?");
    expect(html).toContain("Respuesta parcial");
  });
});
