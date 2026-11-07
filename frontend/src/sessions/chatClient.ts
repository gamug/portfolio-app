import type { ChatClient } from "./SessionController";

async function errorMessage(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { error?: unknown };
    if (typeof data.error === "string" && data.error.trim().length > 0) {
      return data.error;
    }
  } catch {
    // The fallback below is enough for a response without a JSON error.
  }
  return `Chat request failed with status ${response.status}`;
}

export function createChatClient(baseUrl: string): ChatClient {
  const normalized = baseUrl.replace(/\/$/, "");
  return {
    async *streamAnswer(
      question: string,
      sessionId: string,
      signal?: AbortSignal,
    ): AsyncIterable<string> {
      const response = await fetch(`${normalized}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, session_id: sessionId }),
        signal,
      });
      if (!response.ok) {
        throw new Error(await errorMessage(response));
      }
      if (response.body === null) {
        const text = await response.text();
        if (text.length > 0) {
          yield text;
        }
        return;
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            break;
          }
          const text = decoder.decode(value, { stream: true });
          if (text.length > 0) {
            yield text;
          }
        }
        const remaining = decoder.decode();
        if (remaining.length > 0) {
          yield remaining;
        }
      } finally {
        void reader.cancel().catch(() => undefined);
        reader.releaseLock();
      }
    },
  };
}
