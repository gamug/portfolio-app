import { afterEach, describe, expect, it, vi } from "vitest";
import { createRelevanceClient } from "./relevanceClient";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("createRelevanceClient", () => {
  it("loads the relevance state", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ pair_id: "p1", relevant: false }), {
        status: 200,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const relevant = await createRelevanceClient("/api/threads/").getRelevance("s1", "p1");

    expect(fetchMock).toHaveBeenCalledWith("/api/threads/s1/pairs/p1/relevance");
    expect(relevant).toBe(false);
  });

  it("persists the new relevance state", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ pair_id: "p1", relevant: true }), {
        status: 200,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const relevant = await createRelevanceClient("/api/threads").setRelevance("s1", "p1", true);

    expect(fetchMock).toHaveBeenCalledWith("/api/threads/s1/pairs/p1/relevance", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ relevant: true }),
    });
    expect(relevant).toBe(true);
  });

  it("throws on a failed relevance request", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("", { status: 500 })));

    await expect(createRelevanceClient("/api/threads").getRelevance("s1", "p1")).rejects.toThrow(
      "status 500",
    );
  });
});
