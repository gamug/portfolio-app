import type { EraseClient } from "./SessionController";

export function createEraseClient(baseUrl: string): EraseClient {
  const normalized = baseUrl.replace(/\/$/, "");

  const erase = async (sessionId: string, action: "history" | "report"): Promise<void> => {
    const response = await fetch(`${normalized}/${encodeURIComponent(sessionId)}/${action}`, {
      method: "DELETE",
    });
    if (!response.ok) {
      throw new Error(`Erase request failed with status ${response.status}`);
    }
  };

  return {
    eraseHistory: (sessionId: string) => erase(sessionId, "history"),
    eraseReport: (sessionId: string) => erase(sessionId, "report"),
  };
}
