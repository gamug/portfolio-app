import { afterEach, describe, expect, it, vi } from "vitest";
import { createChatClient } from "./chatClient";

afterEach(() => {
  vi.unstubAllGlobals();
});

function streamResponse(chunks: string[]): Response {
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

async function collect(signal?: AbortSignal): Promise<string[]> {
  const chunks: string[] = [];
  for await (const chunk of createChatClient("/api/").streamAnswer("Question", "s1", signal)) {
    chunks.push(chunk);
  }
  return chunks;
}

describe("createChatClient", () => {
  it("sends the question and streams the raw answer", async () => {
    const controller = new AbortController();
    const fetchMock = vi.fn().mockResolvedValue(streamResponse(["Raw ", "answer"]));
    vi.stubGlobal("fetch", fetchMock);

    const chunks = await collect(controller.signal);

    expect(fetchMock).toHaveBeenCalledWith("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: "Question", session_id: "s1" }),
      signal: controller.signal,
    });
    expect(chunks).toEqual(["Raw ", "answer"]);
  });

  it("shows the localized backend error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: "No se pudo consultar el grafo. Inténtalo de nuevo.",
          }),
          { status: 502 },
        ),
      ),
    );

    await expect(collect()).rejects.toThrow("No se pudo consultar el grafo. Inténtalo de nuevo.");
  });

  it("falls back to a status message when the error body is not JSON", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("", { status: 500 })));

    await expect(collect()).rejects.toThrow("status 500");
  });
});
