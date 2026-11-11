import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { Message } from "@openuidev/react-ui";
import { chartReducer, PairAnswer } from "./PairAnswer";
import type { SessionState } from "./SessionController";

const state: SessionState = {
  sessions: [{ id: "s1", title: "Session", createdAt: "2026-11-07T00:00:00Z" }],
  activeSessionId: "s1",
  messages: [],
  report: null,
  relevance: {},
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

const message: Message = {
  id: "p1",
  role: "assistant",
  content:
    'root = Card([text])\ntext = TextContent("Revenue rose from 100 to 150. **March was strongest.**")',
};

function renderPair(initialShowChart = false): string {
  return renderToStaticMarkup(
    <PairAnswer
      message={message}
      state={state}
      onToggleRelevance={() => undefined}
      onDeletePair={() => undefined}
      initialShowChart={initialShowChart}
    />,
  );
}

describe("PairAnswer", () => {
  it("shows the answer text and keeps the chart collapsed by default", () => {
    const html = renderPair();
    expect(html).toContain("Revenue rose from 100 to 150.");
    expect(html).toContain("<strong>March was strongest.</strong>");
    expect(html).toContain("Show chart");
    expect(html).not.toContain("Hide chart");
    expect(html).not.toContain('data-chart-view="open"');
  });

  it("shows the OpenUI chart when the toggle is open", () => {
    const html = renderPair(true);
    expect(html).toContain("Hide chart");
    expect(html).toContain('data-chart-view="open"');
  });

  it("groups the chart toggle, relevance chip and delete action in a compact footer", () => {
    const html = renderPair();
    expect(html).toContain('class="message__footer"');
    expect(html).toContain('class="message__footer-left"');
    expect(html).toMatch(/message__footer-left[\s\S]*Show chart[\s\S]*Relevant for report/);
    expect(html).toMatch(/message__footer[\s\S]*Delete pair/);
  });

  it("keeps the expanded chart above the footer", () => {
    const html = renderPair(true);
    expect(html.indexOf('data-chart-view="open"')).toBeLessThan(html.indexOf("message__footer"));
  });

  it("toggles the chart state", () => {
    expect(chartReducer(false)).toBe(true);
    expect(chartReducer(true)).toBe(false);
  });
});
