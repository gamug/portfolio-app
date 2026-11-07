import { afterEach, describe, expect, it, vi } from "vitest";
import { createReportClient } from "./reportClient";
import type { ReportStreamEvent } from "./SessionController";

afterEach(() => {
  vi.unstubAllGlobals();
});

function sseResponse(chunks: string[]): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });
  return new Response(stream, { status: 200 });
}

async function collect(signal?: AbortSignal): Promise<ReportStreamEvent[]> {
  const events: ReportStreamEvent[] = [];
  for await (const event of createReportClient("/api/threads/").generateReport("s1", signal)) {
    events.push(event);
  }
  return events;
}

describe("createReportClient", () => {
  it("loads the current report from the thread endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          report: {
            openui_lang: "root = Card([])",
            incomplete: false,
            created_at: "2026-11-07T00:00:00Z",
            updated_at: "2026-11-07T00:00:00Z",
          },
        }),
        { status: 200 },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const report = await createReportClient("/api/threads/").getReport("s1");

    expect(fetchMock).toHaveBeenCalledWith("/api/threads/s1/report");
    expect(report?.openui_lang).toBe("root = Card([])");
  });

  it("returns null when the session has no report", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ report: null }), { status: 200 })),
    );

    expect(await createReportClient("/api/threads").getReport("s1")).toBeNull();
  });

  it("throws on a failed report request", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("", { status: 500 })));

    await expect(createReportClient("/api/threads").getReport("s1")).rejects.toThrow("status 500");
  });

  it("streams progress, deltas and done events", async () => {
    const report = {
      openui_lang: "root = Card([])",
      incomplete: false,
      created_at: "2026-11-07T00:00:00Z",
      updated_at: "2026-11-07T00:00:00Z",
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        sseResponse([
          'event: progress\ndata: {"stage":"planning"}\n\n',
          'event: progress\ndata: {"stage":"rendering"}\n\nevent: delta\ndata: {"text":"root = Card(["}',
          '\n\nevent: delta\ndata: {"text":"]"}\n\n',
          `event: done\ndata: ${JSON.stringify({ report })}\n\n`,
        ]),
      );
    vi.stubGlobal("fetch", fetchMock);

    const events = await collect();

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/threads/s1/report/generate",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      }),
    );
    expect(events).toEqual([
      { type: "progress", stage: "planning" },
      { type: "progress", stage: "rendering" },
      { type: "delta", text: "root = Card([" },
      { type: "delta", text: "]" },
      { type: "done", report },
    ]);
  });

  it("passes the abort signal and yields the server error event", async () => {
    const controller = new AbortController();
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        sseResponse([
          'event: progress\ndata: {"stage":"rendering"}\n\n',
          'event: error\ndata: {"error":"No se pudo generar el informe.","incomplete":true}\n\n',
        ]),
      );
    vi.stubGlobal("fetch", fetchMock);

    const events = await collect(controller.signal);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/threads/s1/report/generate",
      expect.objectContaining({ signal: controller.signal }),
    );
    expect(events.at(-1)).toEqual({
      type: "error",
      error: "No se pudo generar el informe.",
      incomplete: true,
    });
  });

  it("uses the localized error from a rejected request", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: "Esta sesión no tiene historial. Empieza primero la exploración de datos.",
          }),
          { status: 400 },
        ),
      ),
    );

    await expect(collect()).rejects.toThrow(
      "Esta sesión no tiene historial. Empieza primero la exploración de datos.",
    );
  });

  it("rejects a stream that ends without done or error", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(sseResponse(['event: delta\ndata: {"text":"root = Card([])"}\n\n'])),
    );

    await expect(collect()).rejects.toThrow("ended unexpectedly");
  });
});
