import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { ReportPanel } from "./ReportPanel";
import type { SessionState } from "./SessionController";

const baseState: SessionState = {
  sessions: [{ id: "s1", title: "Session", createdAt: "2026-11-07T00:00:00Z" }],
  activeSessionId: "s1",
  messages: [
    { id: "q1", role: "user", content: "First question" },
    { id: "p1", role: "assistant", content: "root = Card([])" },
    { id: "q2", role: "user", content: "Second question" },
    { id: "p2", role: "assistant", content: "root = Card([])" },
    { id: "q3", role: "user", content: "Third question" },
    { id: "p3", role: "assistant", content: "root = Card([])" },
    { id: "p4", role: "assistant", content: "root = Card([])" },
  ],
  answers: {},
  report: null,
  reportOutdated: false,
  relevance: { p1: true, p2: false, p3: true, p4: false },
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
  onGenerate: () => undefined,
  onDownload: () => undefined,
  onDismissDownloadNotice: () => undefined,
  onEraseHistory: () => undefined,
  onEraseReport: () => undefined,
  onCancel: () => undefined,
};

function renderPanel(overrides: Partial<SessionState> = {}): string {
  return renderToStaticMarkup(
    <ReportPanel state={{ ...baseState, ...overrides }} {...noopHandlers} />,
  );
}

describe("ReportPanel status", () => {
  it("shows how many answers are marked relevant", () => {
    const html = renderPanel();

    expect(html).toContain("2 of 4 marked relevant");
  });

  it("treats an unrecorded relevance mark as relevant", () => {
    const html = renderPanel({ relevance: { p2: false, p4: false } });

    expect(html).toContain("2 of 4 marked relevant");
  });

  it("hides the relevance count without answers", () => {
    const html = renderPanel({ messages: [], relevance: {} });

    expect(html).not.toContain("marked relevant");
  });

  it("shows an outdated notice when the report predates the latest changes", () => {
    const html = renderPanel({
      report: {
        openui_lang: "root = Card([])",
        incomplete: false,
        created_at: "2026-11-07T00:00:00Z",
        updated_at: "2026-11-07T00:00:00Z",
      },
      reportOutdated: true,
    });

    expect(html).toContain("Report outdated — regenerate to reflect your latest changes.");
    expect(html).toContain('class="report-panel__outdated"');
  });

  it("hides the outdated notice for a current or missing report", () => {
    const reportState = {
      openui_lang: "root = Card([])",
      incomplete: false,
      created_at: "2026-11-07T00:00:00Z",
      updated_at: "2026-11-07T00:00:00Z",
    };

    expect(renderPanel({ report: reportState, reportOutdated: false })).not.toContain(
      "Report outdated",
    );
    expect(renderPanel({ report: null, reportOutdated: true })).not.toContain("Report outdated");
  });
});
