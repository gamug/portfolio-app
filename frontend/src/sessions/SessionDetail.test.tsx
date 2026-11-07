import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { SessionDetail } from "./SessionDetail";
import type { SessionState } from "./SessionController";

const state: SessionState = {
  sessions: [{ id: "s1", title: "Session", createdAt: "2026-11-07T00:00:00Z" }],
  activeSessionId: "s1",
  messages: [{ id: "p1", role: "assistant", content: "root = Card([])" }],
  report: null,
  relevance: { p1: false },
  isLoading: false,
  error: null,
};

describe("SessionDetail relevance control", () => {
  it("renders one relevance toggle per answer with its stored state", () => {
    const html = renderToStaticMarkup(
      <SessionDetail
        state={state}
        onToggleRelevance={() => undefined}
        onDeletePair={() => undefined}
      />,
    );
    expect(html).toContain('data-pair-id="p1"');
    expect(html).toContain("Relevant for report");
    expect(html).toContain('data-delete-pair-id="p1"');
    expect(html).not.toContain('data-pair-id="p1" checked=""');
  });
});
