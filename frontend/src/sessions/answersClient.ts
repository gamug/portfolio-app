export type AnswerItem = {
  pairId: string;
  text: string;
  createdAt: string;
};

export type AnswersClient = {
  getAnswers(sessionId: string): Promise<Record<string, AnswerItem>>;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function toAnswerItem(value: unknown): AnswerItem | null {
  if (
    !isRecord(value) ||
    typeof value.pair_id !== "string" ||
    typeof value.text !== "string" ||
    typeof value.created_at !== "string"
  ) {
    return null;
  }
  return {
    pairId: value.pair_id,
    text: value.text,
    createdAt: value.created_at,
  };
}

export function createAnswersClient(baseUrl: string): AnswersClient {
  const normalized = baseUrl.replace(/\/$/, "");
  return {
    async getAnswers(sessionId: string): Promise<Record<string, AnswerItem>> {
      const response = await fetch(`${normalized}/${encodeURIComponent(sessionId)}/answers`);
      if (!response.ok) {
        throw new Error(`Answers request failed with status ${response.status}`);
      }
      const data = (await response.json()) as unknown;
      if (!isRecord(data) || !Array.isArray(data.answers)) {
        return {};
      }
      const items = data.answers
        .map(toAnswerItem)
        .filter((item): item is AnswerItem => item !== null);
      return Object.fromEntries(items.map((item) => [item.pairId, item]));
    },
  };
}
