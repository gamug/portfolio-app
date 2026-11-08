import type { ReportExporter, SessionReport } from "./SessionController";

const INVALID_FILENAME_CHARACTERS = /[<>:"/\\|?*]/g;
const MAX_NAME_LENGTH = 80;
const REPORT_TEMPLATE_PLACEHOLDERS = ["__REPORT_META__", "__REPORT_DATA__"] as const;

function stripControlCharacters(value: string): string {
  return Array.from(value)
    .filter((character) => {
      const code = character.codePointAt(0) ?? 0;
      return code >= 32 && code !== 127;
    })
    .join("");
}

export function sanitizeSessionName(name: string): string {
  const cleaned = stripControlCharacters(name)
    .replace(INVALID_FILENAME_CHARACTERS, "-")
    .replace(/\s+/g, " ")
    .replace(/^[.\s]+|[.\s]+$/g, "")
    .slice(0, MAX_NAME_LENGTH)
    .trim();
  return cleaned.length > 0 ? cleaned : "report";
}

export function formatDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function reportFileName(sessionName: string, date: Date = new Date()): string {
  return `${sanitizeSessionName(sessionName)}-${formatDate(date)}.html`;
}

function jsonForScript(value: unknown): string {
  return (JSON.stringify(value) ?? "null").replaceAll("<", "\\u003c");
}

export function buildReportHtml(
  template: string,
  sessionName: string,
  report: SessionReport,
  date: Date = new Date(),
): string {
  for (const placeholder of REPORT_TEMPLATE_PLACEHOLDERS) {
    if (!template.includes(placeholder)) {
      throw new Error(`The report template is missing ${placeholder}.`);
    }
  }
  const meta = jsonForScript({ title: sessionName, date: formatDate(date) });
  const data = jsonForScript(report.openui_lang);
  return template.replaceAll("__REPORT_META__", meta).replaceAll("__REPORT_DATA__", data);
}

function withoutInlineCodeContents(html: string): string {
  return html
    .replace(/(<script\b[^>]*>)[\s\S]*?<\/script>/gi, "$1")
    .replace(/(<style\b[^>]*>)[\s\S]*?<\/style>/gi, "$1");
}

function hasExternalCssUrl(css: string): boolean {
  return /(?<![A-Za-z0-9_])url\(\s*["']?(?:https?:)?\/\//i.test(css);
}

export function hasExternalReferences(html: string): boolean {
  const shell = withoutInlineCodeContents(html);
  if (/<[a-z][^>]*(?<![\w-])(?:src|href)\s*=\s*["'](?:https?:)?\/\//i.test(shell)) {
    return true;
  }
  const styleAttributes = [...shell.matchAll(/(?<![\w-])style\s*=\s*["']([^"']*)["']/gi)].map(
    (match) => match[1] ?? "",
  );
  const styleBlocks = [...html.matchAll(/<style\b[^>]*>([\s\S]*?)<\/style>/gi)].map(
    (match) => match[1] ?? "",
  );
  return [...styleAttributes, ...styleBlocks].some(hasExternalCssUrl);
}

export function createReportExporter(templateUrl = "/report-template.html"): ReportExporter {
  let templatePromise: Promise<string> | null = null;

  const loadTemplate = async (): Promise<string> => {
    templatePromise ??= fetch(templateUrl).then(async (response) => {
      if (!response.ok) {
        throw new Error(`Report template request failed with status ${response.status}`);
      }
      return response.text();
    });
    try {
      return await templatePromise;
    } catch (error) {
      templatePromise = null;
      throw error;
    }
  };

  return {
    async download(sessionName: string, report: SessionReport): Promise<void> {
      const template = await loadTemplate();
      const now = new Date();
      const html = buildReportHtml(template, sessionName, report, now);
      if (hasExternalReferences(html)) {
        throw new Error("The report template has external references.");
      }
      const blob = new Blob([html], { type: "text/html" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = reportFileName(sessionName, now);
      anchor.style.display = "none";
      document.body.append(anchor);
      anchor.click();
      anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 0);
    },
  };
}
