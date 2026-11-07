import type { RelevanceClient } from "./SessionController";

async function readRelevant(response: Response): Promise<boolean> {
  if (!response.ok) {
    throw new Error(`Relevance request failed with status ${response.status}`);
  }
  const data = (await response.json()) as { relevant?: unknown };
  return data.relevant === true;
}

export function createRelevanceClient(baseUrl: string): RelevanceClient {
  const normalized = baseUrl.replace(/\/$/, "");
  return {
    async getRelevance(sessionId: string, pairId: string): Promise<boolean> {
      const response = await fetch(
        `${normalized}/${encodeURIComponent(sessionId)}/pairs/${encodeURIComponent(pairId)}/relevance`,
      );
      return readRelevant(response);
    },
    async setRelevance(sessionId: string, pairId: string, relevant: boolean): Promise<boolean> {
      const response = await fetch(
        `${normalized}/${encodeURIComponent(sessionId)}/pairs/${encodeURIComponent(pairId)}/relevance`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ relevant }),
        },
      );
      return readRelevant(response);
    },
  };
}
