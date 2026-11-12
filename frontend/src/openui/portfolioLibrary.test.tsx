import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { Renderer } from "@openuidev/react-lang";
import { ThemeProvider } from "@openuidev/react-ui";
import { portfolioDarkTheme, portfolioLightTheme } from "../theme";
import { portfolioChatLibrary, portfolioReportLibrary } from "./portfolioLibrary";

function render(response: string, library = portfolioReportLibrary) {
  return renderToStaticMarkup(<Renderer response={response} library={library} />);
}

function axisTickLabels(html: string, axis: "x" | "y"): string[] {
  const pattern = new RegExp(`data-chart-tick="${axis}"[^>]*>([^<]+)<`, "g");
  return [...html.matchAll(pattern)].map((match) => (match[1] ?? "").trim());
}

function yTicks(html: string): number[] {
  return axisTickLabels(html, "y").map((label) => Number(label.replaceAll(",", "")));
}

describe("portfolioReportLibrary", () => {
  it("renders signed metrics inside TextContent", () => {
    const html = render('root = Card([t])\nt = TextContent("Return +19.88% and drawdown -1.24%.")');

    expect(html).toContain("answer-text__metric--positive");
    expect(html).toContain("answer-text__metric--negative");
    expect(html).toContain("+19.88%");
    expect(html).toContain("-1.24%");
  });

  it("renders signed metrics inside InlineHeader", () => {
    const html = render('root = Card([h])\nh = InlineHeader("Takeaway +19.88%", "Versus -1.24%")');

    expect(html).toContain("openui-inline-header");
    expect(html).toContain("answer-text__metric--positive");
    expect(html).toContain("answer-text__metric--negative");
  });

  it("renders signed metrics inside table cells", () => {
    const html = render(
      "root = Card([t])\nt = Table([c1, c2])\n" +
        'c1 = Col("Metric", ["Return", "Drawdown"])\n' +
        'c2 = Col("Result", ["+19.88%", "-1.24%"])',
    );

    expect(html).toContain("openui-table");
    expect(html).toContain("answer-text__metric--positive");
    expect(html).toContain("answer-text__metric--negative");
    expect(html).toContain("+19.88%");
    expect(html).toContain("-1.24%");
  });

  it("right-aligns numeric and signed-metric table columns", () => {
    const html = render(
      "root = Card([t])\nt = Table([c1, c2, c3])\n" +
        'c1 = Col("Month", ["January", "February"])\n' +
        'c2 = Col("Revenue", [1200, 1500], "number")\n' +
        'c3 = Col("Return", ["+19.88%", "-1.24%"])',
    );

    expect(html.match(/data-col-align="right"/g) ?? []).toHaveLength(6);
    expect(html.match(/data-col-align="left"/g) ?? []).toHaveLength(3);
    expect(html).toContain("portfolio-table__col--numeric");
    expect(html).toContain("answer-text__metric--positive");
    expect(html).toContain("answer-text__metric--negative");
  });

  it("right-aligns and highlights Unicode-minus metrics in table cells", () => {
    const html = render(
      "root = Card([t])\nt = Table([c1, c2])\n" +
        'c1 = Col("Metric", ["Return", "Drawdown"])\n' +
        'c2 = Col("Result", ["−10.14 %", "-0,1229"])',
    );

    expect(html).toContain("answer-text__metric--negative");
    expect(html).toContain("−10.14 %");
    expect(html.match(/data-col-align="right"/g) ?? []).toHaveLength(3);
    expect(html).toContain("portfolio-table__col--numeric");
  });

  it("scales NAV line charts around the data and explains the axes", () => {
    const html = renderToStaticMarkup(
      <ThemeProvider mode="dark" lightTheme={portfolioLightTheme} darkTheme={portfolioDarkTheme}>
        <Renderer
          response={
            'root = Card([c])\nc = LineChart(["2022-01", "2022-02", "2022-03", "2022-04", "2022-05", "2022-06"], [Series("Portfolio", [0.8213, 0.874, 0.903, 0.951, 0.982, 1.0087])], "natural", "Fecha", "NAV")'
          }
          library={portfolioReportLibrary}
        />
      </ThemeProvider>,
    );

    const ticks = yTicks(html);
    expect(ticks.length).toBeGreaterThanOrEqual(4);
    expect(Math.min(...ticks)).toBeGreaterThan(0.75);
    expect(Math.max(...ticks)).toBeLessThan(1.1);
    expect(axisTickLabels(html, "y")).toEqual(["0.800", "0.850", "0.900", "0.950", "1.000"]);
    expect(html).not.toContain(">0.000<");
    expect(html).toContain("Eje Y: NAV");
    expect(html).toContain("Rango: 0.8213 – 1.0087");
    expect(html).toContain("Eje X: Fecha");
    expect(html).toContain('data-series-legend="Portfolio"');
    expect(html).toContain("0.8213 → 1.0087");
    expect(html).toContain('data-chart-kind="line"');
    expect(html).toContain('height="360"');
    expect(html).toContain("#FB7185");
  });

  it("formats integer area chart y-axis ticks without trailing decimals", () => {
    const html = renderToStaticMarkup(
      <ThemeProvider mode="dark" lightTheme={portfolioLightTheme} darkTheme={portfolioDarkTheme}>
        <Renderer
          response={
            'root = Card([c])\nc = AreaChart(["2022-01", "2022-02", "2022-03", "2022-04", "2022-05", "2022-06", "2022-07", "2022-08", "2022-09", "2022-10"], [Series("Alerts", [107, 110, 93, 66, 168, 100, 79, 86, 111, 58])], "natural", "Fecha", "Alertas")'
          }
          library={portfolioReportLibrary}
        />
      </ThemeProvider>,
    );

    expect(axisTickLabels(html, "y")).toEqual(["0", "50", "100", "150"]);
    expect(axisTickLabels(html, "y").some((label) => label.includes("."))).toBe(false);
    expect(axisTickLabels(html, "x")).not.toContain("2022-09");
    expect(axisTickLabels(html, "x")).toContain("2022-10");
  });

  it("provides the same signed-metric overrides to chat charts", () => {
    const html = render(
      'root = Card([t])\nt = TextContent("Return +19.88% and drawdown -1.24%.")',
      portfolioChatLibrary,
    );

    expect(html).toContain("answer-text__metric--positive");
    expect(html).toContain("answer-text__metric--negative");
  });
});
