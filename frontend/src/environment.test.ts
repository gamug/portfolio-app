import { describe, expect, it } from "vitest";

describe("frontend toolchain", () => {
  it("runs on Node.js 22 or newer", () => {
    expect(Number(process.versions.node.split(".")[0])).toBeGreaterThanOrEqual(22);
  });

  it("resolves the approved OpenUI packages", async () => {
    const lang = await import("@openuidev/react-lang");
    expect(lang).toBeDefined();
  });
});
