import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { createParser, type Library } from "@openuidev/react-lang";
import {
  openuiChatLibrary,
  openuiChatPromptOptions,
  openuiLibrary,
  openuiPromptOptions,
} from "@openuidev/react-ui/genui-lib";

const REPO_ROOT = fileURLToPath(new URL("../..", import.meta.url));
const RESULTS = resolve(REPO_ROOT, "backend/tests/evaluation/local-results");
const CHAT_PROMPT = resolve(RESULTS, "task-019-chat-prompt.txt");
const REPORT_PROMPT = resolve(RESULTS, "task-019-report-prompt.txt");
const CHAT_OUTPUT = resolve(RESULTS, "task-019-chat-output.txt");
const REPORT_OUTPUT = resolve(RESULTS, "task-019-report-output.txt");
const PARSE_REPORT = resolve(RESULTS, "task-019-parse.json");
const SAMPLE_REPORT = resolve(REPO_ROOT, "frontend/spikes/export/sample-report.openui");
const CHART_COMPONENTS = [
  "BarChart",
  "LineChart",
  "AreaChart",
  "HorizontalBarChart",
  "PieChart",
  "RadialChart",
  "ScatterChart",
  "SingleStackedBarChart",
];

function parseOutput(text: string, library: Library) {
  try {
    const result = createParser(library.toJSONSchema(), library.root).parse(text);
    return {
      parsed: true,
      root_present: result.root !== null,
      errors: result.meta.errors.length,
      statements: result.meta.statementCount,
      incomplete: result.meta.incomplete,
    };
  } catch (error) {
    return {
      parsed: false,
      root_present: false,
      errors: 1,
      statements: 0,
      incomplete: true,
      error: String(error),
    };
  }
}

function plotAnalysis(text: string) {
  const chartComponents = CHART_COMPONENTS.filter((name) =>
    new RegExp(`\\b${name}\\s*\\(`).test(text),
  );
  return {
    chart_components: chartComponents,
    has_chart: chartComponents.length > 0,
    has_series: /\bSeries\s*\(/.test(text),
    expected_values_present: ["100", "120", "150"].every((value) =>
      new RegExp(`\\b${value}\\b`).test(text),
    ),
    has_table: /\bTable\s*\(/.test(text),
  };
}

describe("TASK-019 OpenUI prompt and parser", () => {
  it("writes the locally generated prompts", () => {
    mkdirSync(RESULTS, { recursive: true });
    const chatPrompt = openuiChatLibrary.prompt(openuiChatPromptOptions);
    const reportPrompt = openuiLibrary.prompt(openuiPromptOptions);
    writeFileSync(CHAT_PROMPT, chatPrompt, "utf-8");
    writeFileSync(REPORT_PROMPT, reportPrompt, "utf-8");
    expect(chatPrompt.length).toBeGreaterThan(1000);
    expect(reportPrompt.length).toBeGreaterThan(1000);
  });

  it("parses the synthetic export sample", () => {
    const result = parseOutput(readFileSync(SAMPLE_REPORT, "utf-8"), openuiLibrary);
    expect(result.parsed).toBe(true);
    expect(result.root_present).toBe(true);
    expect(result.errors).toBe(0);
  });

  it.skipIf(!existsSync(CHAT_OUTPUT) || !existsSync(REPORT_OUTPUT))(
    "parses the DeepSeek outputs and records the plot analysis",
    () => {
      const chatText = readFileSync(CHAT_OUTPUT, "utf-8");
      const reportText = readFileSync(REPORT_OUTPUT, "utf-8");
      const chat = parseOutput(chatText, openuiChatLibrary);
      const report = parseOutput(reportText, openuiLibrary);
      const parsedWithoutErrors = [chat, report].filter(
        (result) => result.parsed && result.errors === 0 && result.root_present,
      ).length;
      const result = {
        share_parsed_without_errors: `${parsedWithoutErrors}/2`,
        chat,
        report,
        plot: plotAnalysis(reportText),
      };
      writeFileSync(PARSE_REPORT, `${JSON.stringify(result, null, 2)}\n`, "utf-8");
      expect(parsedWithoutErrors).toBe(2);
    },
  );
});
