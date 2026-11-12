import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { Message } from "@openuidev/react-ui";
import {
  chartReducer,
  INITIAL_SPARQL_STATE,
  needsSparqlFetch,
  PairAnswer,
  SparqlQueriesPanel,
  SPARQL_ERROR,
  sparqlReducer,
  type SparqlState,
} from "./PairAnswer";
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

  it("opens and closes the SPARQL viewer", () => {
    expect(renderPair()).toContain("Show SPARQL query");
    const opened = sparqlReducer(INITIAL_SPARQL_STATE, { type: "toggle" });
    expect(opened.open).toBe(true);
    const closed = sparqlReducer(opened, { type: "toggle" });
    expect(closed.open).toBe(false);
  });

  it("loads SPARQL queries once and reuses the cache when reopened", () => {
    const opened = sparqlReducer(INITIAL_SPARQL_STATE, { type: "toggle" });
    expect(needsSparqlFetch(opened)).toBe(true);

    const loading = sparqlReducer(opened, { type: "loading" });
    const loaded = sparqlReducer(loading, {
      type: "loaded",
      queries: ["SELECT * WHERE { ?s ?p ?o }"],
    });
    expect(needsSparqlFetch(loaded)).toBe(false);

    const closed = sparqlReducer(loaded, { type: "toggle" });
    const reopened = sparqlReducer(closed, { type: "toggle" });
    expect(reopened.queries).toEqual(["SELECT * WHERE { ?s ?p ?o }"]);
    expect(needsSparqlFetch(reopened)).toBe(false);
  });

  it("renders every cached SPARQL query with a Copy button", () => {
    const state: SparqlState = {
      ...INITIAL_SPARQL_STATE,
      open: true,
      queries: ["SELECT * WHERE { ?s ?p ?o }", "ASK { ?s ?p ?o }"],
    };
    const html = renderToStaticMarkup(
      <SparqlQueriesPanel state={state} copiedIndex={0} onCopy={() => undefined} />,
    );

    expect(html.match(/<pre><code>/g) ?? []).toHaveLength(2);
    expect(html).toContain("SPARQL query 1");
    expect(html).toContain("SPARQL query 2");
    expect(html).toContain("Copied");
    expect(html).toContain("Copy");
  });

  it("shows a loading state while the SPARQL query is fetched", () => {
    const loading = sparqlReducer(sparqlReducer(INITIAL_SPARQL_STATE, { type: "toggle" }), {
      type: "loading",
    });
    const html = renderToStaticMarkup(
      <SparqlQueriesPanel state={loading} copiedIndex={null} onCopy={() => undefined} />,
    );

    expect(html).toContain("Loading SPARQL query…");
  });

  it("shows an empty state when no SPARQL query was recorded", () => {
    const state: SparqlState = {
      ...INITIAL_SPARQL_STATE,
      open: true,
      queries: [],
    };
    const html = renderToStaticMarkup(
      <SparqlQueriesPanel state={state} copiedIndex={null} onCopy={() => undefined} />,
    );

    expect(html).toContain("No SPARQL query recorded for this answer.");
  });

  it("shows a user-safe error when SPARQL loading fails", () => {
    const opened = sparqlReducer(INITIAL_SPARQL_STATE, { type: "toggle" });
    const failed = sparqlReducer(sparqlReducer(opened, { type: "loading" }), {
      type: "failed",
      error: SPARQL_ERROR,
    });
    const html = renderToStaticMarkup(
      <SparqlQueriesPanel state={failed} copiedIndex={null} onCopy={() => undefined} />,
    );

    expect(html).toContain('role="alert"');
    expect(html).toContain(SPARQL_ERROR);
  });
});
