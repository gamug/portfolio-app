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

  it("renders inline code inside bold text", () => {
    const html = renderToStaticMarkup(<AnswerText text={"**Alpha `:Beta` Gamma**"} />);
    expect(html).toContain("<strong>Alpha <code>:Beta</code> Gamma</strong>");
    expect(html).not.toContain("`");
  });

  it("renders italics inside bold text", () => {
    const html = renderToStaticMarkup(<AnswerText text={"**Alpha *Beta* Gamma**"} />);
    expect(html).toContain("<strong>Alpha <em>Beta</em> Gamma</strong>");
  });

  it("renders plain bold text", () => {
    const html = renderToStaticMarkup(<AnswerText text="**Alpha**" />);
    expect(html).toContain("<strong>Alpha</strong>");
  });

  it("renders plain inline code", () => {
    const html = renderToStaticMarkup(<AnswerText text="`Alpha`" />);
    expect(html).toContain("<code>Alpha</code>");
  });

  it("renders plain italics", () => {
    const html = renderToStaticMarkup(<AnswerText text="*Alpha*" />);
    expect(html).toContain("<em>Alpha</em>");
  });

  it("leaves unmatched markers as text", () => {
    const html = renderToStaticMarkup(<AnswerText text={"**Alpha `Beta *Gamma"} />);
    expect(html).toContain("**Alpha `Beta *Gamma");
    expect(html).not.toContain("<strong>");
    expect(html).not.toContain("<code>");
    expect(html).not.toContain("<em>");
  });
});
