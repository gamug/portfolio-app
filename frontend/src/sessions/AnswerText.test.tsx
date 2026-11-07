import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { AnswerText } from "./AnswerText";

describe("AnswerText", () => {
  it("renders line breaks, bold text, lists and markdown tables", () => {
    const html = renderToStaticMarkup(
      <AnswerText
        text={
          "Revenue rose from 100 to 150.\n\n**March was the strongest month.**\n\n" +
          "- January\n- February\n\n" +
          "| Month | Revenue |\n| --- | --- |\n| January | 100 |\n| March | 150 |"
        }
      />,
    );

    expect(html).toContain("Revenue rose from 100 to 150.");
    expect(html).toContain("<strong>March was the strongest month.</strong>");
    expect(html).toContain("<ul>");
    expect(html).toContain("<li>January</li>");
    expect(html).toContain("<table>");
    expect(html).toContain("<th");
    expect(html).toContain("<td>150</td>");
  });
});
