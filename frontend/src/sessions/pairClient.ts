import type { PairClient } from "./SessionController";

export function createPairClient(baseUrl: string): PairClient {
  const normalized = baseUrl.replace(/\/$/, "");
  return {
    async deletePair(sessionId: string, pairId: string): Promise<void> {
      const response = await fetch(
        `${normalized}/${encodeURIComponent(sessionId)}/pairs/${encodeURIComponent(pairId)}`,
        { method: "DELETE" },
      );
      if (!response.ok) {
        throw new Error(`Pair delete failed with status ${response.status}`);
      }
    },
  };
}
