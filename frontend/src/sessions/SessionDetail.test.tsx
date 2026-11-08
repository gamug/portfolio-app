import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { SessionDetail } from "./SessionDetail";
import type { SessionState } from "./SessionController";

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
};

function renderDetail(overrides: Partial<SessionState> = {}): string {
  return renderToStaticMarkup(
    <SessionDetail
      state={{ ...baseState, ...overrides }}
      onToggleRelevance={() => undefined}
      onDeletePair={() => undefined}
      onSendQuestion={() => undefined}
      onGenerateReport={() => undefined}
      onDownloadReport={() => undefined}
      onCancelReport={() => undefined}
    />,
  );
}

describe("SessionDetail chat and report panels", () => {
  it("renders the chat and report panels side by side with the input and actions", () => {
    const html = renderDetail();
    expect(html).toContain('aria-label="Chat"');
    expect(html).toContain('aria-label="Report"');
    expect(html).toContain('aria-label="Question"');
    expect(html).toContain("Send");
    expect(html).toContain("Generate Report");
    expect(html).not.toContain("Download Report");
    expect(html).toContain("No report yet.");
    expect(html).toContain('data-report-view="empty"');
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
