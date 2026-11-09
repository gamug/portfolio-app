import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { SessionList, SessionListDeleteConfirmation } from "./SessionList";
import type { SessionState } from "./SessionController";

const baseState: SessionState = {
  sessions: [
    { id: "s1", title: "Session one", createdAt: "2026-11-07T00:00:00Z" },
    { id: "s2", title: "Session two", createdAt: "2026-11-07T00:00:00Z" },
  ],
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

function renderList(overrides: Partial<SessionState> = {}): string {
  return renderToStaticMarkup(
    <SessionList
      state={{ ...baseState, ...overrides }}
      onCreate={() => undefined}
      onSelect={() => undefined}
      onRename={() => undefined}
      onDelete={() => undefined}
      onDismissError={() => undefined}
    />,
  );
}

function buttonForText(html: string, text: string): string {
  const match = html.match(new RegExp(`<button[^>]*>${text}</button>`));
  if (match === null) {
    throw new Error(`No button with text ${text}`);
  }
  return match[0];
}

function buttonForAttribute(html: string, attribute: string): string {
  const match = html.match(new RegExp(`<button[^>]*${attribute}[^>]*>`));
  if (match === null) {
    throw new Error(`No button with ${attribute}`);
  }
  return match[0];
}

describe("SessionList session lock", () => {
  it("keeps the session controls enabled when idle", () => {
    const html = renderList();
    expect(html).not.toContain("Wait for the current action to finish.");
    expect(buttonForText(html, "New session")).not.toContain('disabled=""');
    expect(buttonForAttribute(html, 'class="session-list__select"')).not.toContain('disabled=""');
    expect(buttonForAttribute(html, 'aria-label="Rename Session one"')).not.toContain(
      'disabled=""',
    );
    expect(buttonForAttribute(html, 'aria-label="Delete Session one"')).not.toContain(
      'disabled=""',
    );
  });

  const busyStates: Array<[string, Partial<SessionState>]> = [
    ["a chat answer is pending", { isSendingChat: true }],
    ["a report is being generated", { isGeneratingReport: true }],
    ["a session action is loading", { isLoading: true }],
  ];

  it.each(busyStates)("disables every session control while %s", (_label, overrides) => {
    const html = renderList(overrides);
    expect(html).toContain("Wait for the current action to finish.");
    expect(buttonForText(html, "New session")).toContain('disabled=""');
    expect(buttonForAttribute(html, 'class="session-list__select"')).toContain('disabled=""');
    expect(buttonForAttribute(html, 'aria-label="Rename Session one"')).toContain('disabled=""');
    expect(buttonForAttribute(html, 'aria-label="Delete Session one"')).toContain('disabled=""');
  });

  it("disables both delete confirmation buttons while busy", () => {
    const busy = renderToStaticMarkup(
      <SessionListDeleteConfirmation
        disabled
        onConfirm={() => undefined}
        onCancel={() => undefined}
      />,
    );
    expect(busy).toContain('role="alertdialog"');
    expect(busy.match(/disabled=""/g) ?? []).toHaveLength(2);

    const idle = renderToStaticMarkup(
      <SessionListDeleteConfirmation
        disabled={false}
        onConfirm={() => undefined}
        onCancel={() => undefined}
      />,
    );
    expect(idle).not.toContain('disabled=""');
  });
});
