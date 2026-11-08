import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { SessionReport } from "./SessionController";
import {
  buildReportHtml,
  createReportExporter,
  formatDate,
  hasExternalReferences,
  reportFileName,
  sanitizeSessionName,
} from "./reportExport";

const TEMPLATE = `<!doctype html>
<html>
  <head><title>Report</title><style>body{background:#fff}</style></head>
  <body>
    <div id="root"></div>
    <script type="application/json" id="report-meta">__REPORT_META__</script>
    <script type="application/json" id="report-data">__REPORT_DATA__</script>
    <script type="module">window.__report=true;</script>
  </body>
</html>`;

function report(openuiLang = "root = Card([])"): SessionReport {
  return {
    openui_lang: openuiLang,
    incomplete: false,
    created_at: "2026-11-07T00:00:00Z",
    updated_at: "2026-11-07T00:00:00Z",
  };
}

const REAL_TEMPLATE_PATH = [
  resolve(process.cwd(), "public/report-template.html"),
  resolve(process.cwd(), "frontend/public/report-template.html"),
].find((candidate) => existsSync(candidate));

function stubDownloadEnvironment(template: string) {
  const fetchMock = vi.fn().mockResolvedValue(new Response(template, { status: 200 }));
  vi.stubGlobal("fetch", fetchMock);
  const anchor = {
    href: "",
    download: "",
    style: { display: "" },
    click: vi.fn(),
    remove: vi.fn(),
  };
  const append = vi.fn();
  vi.stubGlobal("document", {
    createElement: vi.fn(() => anchor),
    body: { append },
  });
  const createObjectURL = vi.fn((blob: Blob) => {
    void blob;
    return "blob:report";
  });
  const revokeObjectURL = vi.fn();
  vi.stubGlobal("URL", { createObjectURL, revokeObjectURL });
  return { fetchMock, anchor, append, createObjectURL, revokeObjectURL };
}

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("report export", () => {
  it("names the file from the session and the download date", () => {
    expect(reportFileName("Q3 sales", new Date(2026, 10, 5))).toBe("Q3 sales-2026-11-05.html");
    expect(formatDate(new Date(2026, 0, 9))).toBe("2026-01-09");
  });

  it("sanitizes filesystem-invalid session names", () => {
    const name = sanitizeSessionName(' Q3 / sales: "x" ? * < > | \\ end. ');
    expect(name).not.toMatch(/[<>:"/\\|?*]/);
    expect(name.startsWith(".")).toBe(false);
    expect(name.endsWith(".")).toBe(false);
    expect(name.length).toBeGreaterThan(0);
    expect(sanitizeSessionName("   ")).toBe("report");
  });

  it("builds a self-contained HTML with the report content and metadata", () => {
    const html = buildReportHtml(TEMPLATE, "Q3 sales", report(), new Date(2026, 10, 5));
    expect(html).toContain("Q3 sales");
    expect(html).toContain("2026-11-05");
    expect(html).toContain("root = Card([])");
    expect(html).not.toContain("__REPORT_");
    expect(hasExternalReferences(html)).toBe(false);
  });

  it("escapes a closing script sequence in the report content", () => {
    const html = buildReportHtml(
      TEMPLATE,
      "Q3 sales",
      report('root = Card([text])\ntext = TextContent("</script>")'),
      new Date(2026, 10, 5),
    );
    expect(html).not.toContain('</script>"');
    expect(html).toContain("\\u003c/script>");
  });

  it("detects real external resource loads", () => {
    expect(hasExternalReferences('<link rel="stylesheet" href="https://x/y.css">')).toBe(true);
    expect(hasExternalReferences('<script src="//x/y.js"></script>')).toBe(true);
    expect(hasExternalReferences("<style>body{background:url(https://x/y.png)}</style>")).toBe(
      true,
    );
    expect(hasExternalReferences('<div style="background:url(https://x/y.png)"></div>')).toBe(true);
    expect(
      hasExternalReferences("<style>body{background:url(data:image/png;base64,abc)}</style>"),
    ).toBe(false);
    expect(hasExternalReferences("<style>body{background:myurl(https://x/y.png)}</style>")).toBe(
      false,
    );
  });

  it("ignores documentation text and user-provided report text", () => {
    const documentation =
      "<script>const a = '@OpenUrl(\"https://example.com\")'; " +
      "const b = 'Action([@OpenUrl(\"https://example.com\"), ...';</script>";
    expect(hasExternalReferences(documentation)).toBe(false);
    expect(hasExternalReferences('<div>@OpenUrl("https://example.com")</div>')).toBe(false);

    const reportText = 'root = Card([text])\ntext = TextContent("@OpenUrl(https://example.com)")';
    const html = buildReportHtml(TEMPLATE, "Q3 sales", report(reportText), new Date(2026, 10, 5));
    expect(html).toContain("@OpenUrl(https://example.com)");
    expect(hasExternalReferences(html)).toBe(false);
  });

  it("rejects a template without both placeholders", () => {
    expect(() => buildReportHtml("<html></html>", "Q3 sales", report())).toThrow("missing");
  });

  it("fetches the template and triggers a named HTML download", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 10, 5, 12));
    const { fetchMock, anchor, append, createObjectURL, revokeObjectURL } =
      stubDownloadEnvironment(TEMPLATE);

    await createReportExporter("/report-template.html").download("Q3 sales", report());

    expect(fetchMock).toHaveBeenCalledWith("/report-template.html");
    expect(createObjectURL).toHaveBeenCalledTimes(1);
    expect(anchor.download).toBe("Q3 sales-2026-11-05.html");
    expect(anchor.href).toBe("blob:report");
    expect(append).toHaveBeenCalledWith(anchor);
    expect(anchor.click).toHaveBeenCalledTimes(1);
    expect(anchor.remove).toHaveBeenCalledTimes(1);
    vi.runAllTimers();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:report");
  });

  it.skipIf(REAL_TEMPLATE_PATH === undefined)(
    "runs the real built template through the full download path",
    async () => {
      if (REAL_TEMPLATE_PATH === undefined) {
        return;
      }
      vi.useFakeTimers();
      vi.setSystemTime(new Date(2026, 10, 5, 12));
      const template = readFileSync(REAL_TEMPLATE_PATH, "utf8");
      const sample = 'root = Card([text])\ntext = TextContent("Revenue rose from 100 to 150.")';
      const { anchor, append, createObjectURL, revokeObjectURL } =
        stubDownloadEnvironment(template);

      await createReportExporter("/report-template.html").download("Q3 sales", report(sample));

      expect(anchor.download).toBe("Q3 sales-2026-11-05.html");
      expect(anchor.href).toBe("blob:report");
      expect(append).toHaveBeenCalledWith(anchor);
      expect(anchor.click).toHaveBeenCalledTimes(1);
      const blob = createObjectURL.mock.calls[0]?.[0];
      if (!(blob instanceof Blob)) {
        throw new Error("expected the exporter to create a Blob");
      }
      const html = await blob.text();
      expect(html).toContain("Revenue rose from 100 to 150.");
      expect(html).not.toContain("__REPORT_");
      expect(hasExternalReferences(html)).toBe(false);
      vi.runAllTimers();
      expect(revokeObjectURL).toHaveBeenCalledWith("blob:report");
    },
  );
});
