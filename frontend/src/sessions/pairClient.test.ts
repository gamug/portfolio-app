import { afterEach, describe, expect, it, vi } from "vitest";
import { createPairClient } from "./pairClient";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("createPairClient", () => {
  it("deletes the pair through the thread endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    await createPairClient("/api/threads/").deletePair("s1", "p1");

    expect(fetchMock).toHaveBeenCalledWith("/api/threads/s1/pairs/p1", {
      method: "DELETE",
    });
  });

  it("throws on a failed delete", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("", { status: 500 })));

    await expect(createPairClient("/api/threads").deletePair("s1", "p1")).rejects.toThrow(
      "status 500",
    );
  });
});
