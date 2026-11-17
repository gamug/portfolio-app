import { afterEach, describe, expect, it, vi } from "vitest";
import { createAnswersClient } from "./answersClient";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("createAnswersClient", () => {
  it("loads the cleaned analytical text keyed by pair id", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          answers: [
            {
              pair_id: "p1",
              text: "Revenue rose from 100 to 150.",
              created_at: "2026-11-07T00:00:00Z",
            },
            {
              pair_id: "p2",
              text: "March was the strongest month.",
              created_at: "2026-11-07T00:01:00Z",
            },
          ],
        }),
        { status: 200 },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const answers = await createAnswersClient("/api/threads/").getAnswers("s1");

    expect(fetchMock).toHaveBeenCalledWith("/api/threads/s1/answers");
    expect(answers).toEqual({
      p1: {
        pairId: "p1",
        text: "Revenue rose from 100 to 150.",
        createdAt: "2026-11-07T00:00:00Z",
      },
      p2: {
        pairId: "p2",
        text: "March was the strongest month.",
        createdAt: "2026-11-07T00:01:00Z",
      },
    });
  });

  it("returns an empty record when the response has no answers", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ answers: [] }), { status: 200 })),
    );

    const answers = await createAnswersClient("/api/threads").getAnswers("s1");

    expect(answers).toEqual({});
  });

  it("skips malformed answer entries", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            answers: [
              { pair_id: "p1", text: "Valid.", created_at: "2026-11-07T00:00:00Z" },
              { pair_id: "p2", text: "Missing timestamp." },
            ],
          }),
          { status: 200 },
        ),
      ),
    );

    const answers = await createAnswersClient("/api/threads").getAnswers("s1");

    expect(Object.keys(answers)).toEqual(["p1"]);
  });

  it("throws on a failed answers request", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("", { status: 404 })));

    await expect(createAnswersClient("/api/threads").getAnswers("missing")).rejects.toThrow(
      "status 404",
    );
  });
});
