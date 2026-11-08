import { afterEach, describe, expect, it, vi } from "vitest";
import { createEraseClient } from "./eraseClient";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("createEraseClient", () => {
  it("erases the history through the session endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    await createEraseClient("/api/threads/").eraseHistory("s1");

    expect(fetchMock).toHaveBeenCalledWith("/api/threads/s1/history", {
      method: "DELETE",
    });
  });

  it("erases the report through the session endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    await createEraseClient("/api/threads").eraseReport("s1");

    expect(fetchMock).toHaveBeenCalledWith("/api/threads/s1/report", {
      method: "DELETE",
    });
  });

  it("throws on a failed erase", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("", { status: 500 })));

    await expect(createEraseClient("/api/threads").eraseHistory("s1")).rejects.toThrow(
      "status 500",
    );
  });
});
