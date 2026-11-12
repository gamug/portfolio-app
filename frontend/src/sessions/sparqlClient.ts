export interface SparqlClient {
  getSparql(sessionId: string, pairId: string): Promise<string[]>;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

async function readQueries(response: Response): Promise<string[]> {
  if (!response.ok) {
    throw new Error(`SPARQL request failed with status ${response.status}`);
  }
  const data = (await response.json()) as unknown;
  if (!isRecord(data) || !Array.isArray(data.queries)) {
    return [];
  }
  return data.queries.filter((query): query is string => typeof query === "string");
}

export function createSparqlClient(baseUrl: string): SparqlClient {
  const normalized = baseUrl.replace(/\/$/, "");
  return {
    async getSparql(sessionId: string, pairId: string): Promise<string[]> {
      const response = await fetch(
        `${normalized}/${encodeURIComponent(sessionId)}/pairs/${encodeURIComponent(pairId)}/sparql`,
      );
      return readQueries(response);
    },
  };
}
