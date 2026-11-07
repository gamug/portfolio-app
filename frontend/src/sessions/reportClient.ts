import type { ReportClient, ReportStreamEvent, SessionReport } from "./SessionController";

async function reportError(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { error?: unknown };
    if (typeof data.error === "string" && data.error.trim().length > 0) {
      return data.error;
    }
  } catch {
    // The fallback below is enough for a response without a JSON error.
  }
  return `Report request failed with status ${response.status}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isReport(value: unknown): value is SessionReport {
  return (
    isRecord(value) &&
    typeof value.openui_lang === "string" &&
    typeof value.incomplete === "boolean" &&
    typeof value.created_at === "string" &&
    typeof value.updated_at === "string"
  );
}

function parseEvent(block: string): ReportStreamEvent | null {
  let name = "";
  const data: string[] = [];
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) {
      name = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      data.push(line.slice("data:".length).trimStart());
    }
  }
  if (name.length === 0 || data.length === 0) {
    return null;
  }
  let payload: unknown;
  try {
    payload = JSON.parse(data.join("\n"));
  } catch {
    throw new Error("The report stream returned invalid data.");
  }
  if (!isRecord(payload)) {
    throw new Error("The report stream returned invalid data.");
  }
  if (name === "progress") {
    const stage = payload.stage;
    if (stage !== "planning" && stage !== "rendering") {
      throw new Error("The report stream returned an invalid progress stage.");
    }
    return { type: "progress", stage };
  }
  if (name === "delta") {
    if (typeof payload.text !== "string") {
      throw new Error("The report stream returned an invalid delta.");
    }
    return { type: "delta", text: payload.text };
  }
  if (name === "done") {
    if (!isReport(payload.report)) {
      throw new Error("The report stream returned an invalid report.");
    }
    return { type: "done", report: payload.report };
  }
  if (name === "error") {
    if (typeof payload.error !== "string" || typeof payload.incomplete !== "boolean") {
      throw new Error("The report stream returned an invalid error.");
    }
    return { type: "error", error: payload.error, incomplete: payload.incomplete };
  }
  return null;
}

async function* readEvents(response: Response): AsyncIterable<ReportStreamEvent> {
  if (response.body === null) {
    throw new Error("The report stream returned no body.");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      buffer = `${buffer}${decoder.decode(value, { stream: true })}`.replaceAll("\r\n", "\n");
      let boundary = buffer.indexOf("\n\n");
      while (boundary !== -1) {
        const block = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const event = parseEvent(block);
        if (event !== null) {
          yield event;
        }
        boundary = buffer.indexOf("\n\n");
      }
    }
    buffer = `${buffer}${decoder.decode()}`.replaceAll("\r\n", "\n");
    const event = parseEvent(buffer);
    if (event !== null) {
      yield event;
    }
  } finally {
    void reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}

export function createReportClient(baseUrl: string): ReportClient {
  const normalized = baseUrl.replace(/\/$/, "");
  return {
    async getReport(sessionId: string): Promise<SessionReport | null> {
      const response = await fetch(`${normalized}/${encodeURIComponent(sessionId)}/report`);
      if (!response.ok) {
        throw new Error(await reportError(response));
      }
      const data = (await response.json()) as { report?: SessionReport | null };
      return data.report ?? null;
    },
    async *generateReport(
      sessionId: string,
      signal?: AbortSignal,
    ): AsyncIterable<ReportStreamEvent> {
      const response = await fetch(
        `${normalized}/${encodeURIComponent(sessionId)}/report/generate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: "{}",
          signal,
        },
      );
      if (!response.ok) {
        throw new Error(await reportError(response));
      }
      let terminal = false;
      for await (const event of readEvents(response)) {
        if (event.type === "done" || event.type === "error") {
          terminal = true;
        }
        yield event;
      }
      if (!terminal) {
        throw new Error("The report stream ended unexpectedly.");
      }
    },
  };
}
