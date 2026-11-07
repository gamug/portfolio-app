import { describe, expect, it } from "vitest";
import { extractAnswerText, messageText } from "./answerText";

const SAMPLE_OPENUI = `root = Card([header, summary, chart, followUps])
header = CardHeader("Monthly Revenue", "January – March")
summary = TextContent("Revenue rose from 100 in January to 150 in March. **March was the strongest month.**")
chart = BarChart(labels, [revenueSeries], "grouped", "Month", "Revenue")
labels = ["January", "February", "March"]
revenueSeries = Series("Revenue", [100, 120, 150])
followUps = FollowUpBlock([fu1])
fu1 = FollowUpItem("Show this as a trend line")`;

describe("answer text", () => {
  it("extracts the narrative and headings without chart or follow-up text", () => {
    const text = extractAnswerText(SAMPLE_OPENUI);
    expect(text).toContain("Monthly Revenue");
    expect(text).toContain("January – March");
    expect(text).toContain("March was the strongest month");
    expect(text).not.toContain("BarChart");
    expect(text).not.toContain("Show this as a trend line");
  });

  it("returns an empty string when the OpenUI Lang has no text components", () => {
    expect(extractAnswerText("root = Card([])")).toBe("");
  });

  it("reads string content", () => {
    expect(messageText({ id: "p1", role: "assistant", content: "answer" })).toBe("answer");
  });
});
