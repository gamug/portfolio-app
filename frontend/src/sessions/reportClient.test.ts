import { afterEach, describe, expect, it, vi } from "vitest";
import { createReportClient } from "./reportClient";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("createReportClient", () => {
  it("loads the current report from the thread endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          report: {
            openui_lang: "root = Card([])",
            incomplete: false,
            created_at: "2026-11-07T00:00:00Z",
            updated_at: "2026-11-07T00:00:00Z",
          },
        }),
        { status: 200 },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const report = await createReportClient("/api/threads/").getReport("s1");

    expect(fetchMock).toHaveBeenCalledWith("/api/threads/s1/report");
    expect(report?.openui_lang).toBe("root = Card([])");
  });

  it("returns null when the session has no report", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ report: null }), { status: 200 })),
    );

    expect(await createReportClient("/api/threads").getReport("s1")).toBeNull();
  });

  it("throws on a failed report request", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("", { status: 500 })));

    await expect(createReportClient("/api/threads").getReport("s1")).rejects.toThrow("status 500");
  });
});
