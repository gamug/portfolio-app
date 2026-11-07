import type { ReportClient, SessionReport } from "./SessionController";

export function createReportClient(baseUrl: string): ReportClient {
  const normalized = baseUrl.replace(/\/$/, "");
  return {
    async getReport(sessionId: string): Promise<SessionReport | null> {
      const response = await fetch(`${normalized}/${encodeURIComponent(sessionId)}/report`);
      if (!response.ok) {
        throw new Error(`Report request failed with status ${response.status}`);
      }
      const data = (await response.json()) as { report?: SessionReport | null };
      return data.report ?? null;
    },
  };
}
