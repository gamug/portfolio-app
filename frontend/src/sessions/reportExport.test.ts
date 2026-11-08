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

  it("detects external references", () => {
    expect(hasExternalReferences('<script src="https://cdn.example/report.js"></script>')).toBe(
      true,
    );
    expect(hasExternalReferences("body{background:url(https://cdn.example/bg.png)}")).toBe(true);
    expect(hasExternalReferences(TEMPLATE)).toBe(false);
  });

  it("rejects a template without both placeholders", () => {
    expect(() => buildReportHtml("<html></html>", "Q3 sales", report())).toThrow("missing");
  });

  it("fetches the template and triggers a named HTML download", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 10, 5, 12));
    const fetchMock = vi.fn().mockResolvedValue(new Response(TEMPLATE, { status: 200 }));
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
    const createObjectURL = vi.fn(() => "blob:report");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", { createObjectURL, revokeObjectURL });

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
});
