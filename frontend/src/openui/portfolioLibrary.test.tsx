import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { Renderer } from "@openuidev/react-lang";
import { ThemeProvider } from "@openuidev/react-ui";
import { portfolioDarkTheme, portfolioLightTheme } from "../theme";
import {
  portfolioChatLibrary,
  portfolioReportLibrary,
  toggleSeriesVisibility,
} from "./portfolioLibrary";

function render(response: string, library = portfolioReportLibrary) {
  return renderToStaticMarkup(<Renderer response={response} library={library} />);
}

function barFills(html: string): string[] {
  return [...html.matchAll(/<rect[^>]*class="portfolio-chart__bar"[^>]*fill="([^"]+)"/g)].map(
    (match) => match[1] ?? "",
  );
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

  it("colors every single-series bar distinctly instead of using flat blue", () => {
    const html = renderToStaticMarkup(
      <ThemeProvider mode="dark" lightTheme={portfolioLightTheme} darkTheme={portfolioDarkTheme}>
        <Renderer
          response={
            'root = Card([c])\nc = BarChart(["P1", "P2", "P3"], [Series("Alerts", [10, 20, 30])], "grouped", "Period", "Alerts")'
          }
          library={portfolioReportLibrary}
        />
      </ThemeProvider>,
    );

    expect(html).toContain('data-chart-kind="bar"');
    expect(barFills(html)).toEqual(["#34D399", "#38BDF8", "#A78BFA"]);
    expect(html).not.toContain("#60A5FA");
    expect(html).not.toContain("#2563EB");
  });

  it("colors horizontal bars distinctly and labels the value axis", () => {
    const html = render(
      'root = Card([c])\nc = HorizontalBarChart(["Alpha", "Beta", "Gamma"], [Series("Return", [12, 18, 25])], "grouped", "Strategy", "Return (%)")',
    );

    expect(html).toContain('data-chart-kind="horizontal-bar"');
    expect(barFills(html)).toEqual(["#10B981", "#0284C7", "#7C3AED"]);
    expect(html).toContain("Eje X: Return (%)");
    expect(html).toContain("Eje Y: Strategy");
    expect(html).toMatch(/data-chart-tick="x"/);
  });

  it("colors multi-series bars by series and exposes legend toggles", () => {
    const html = render(
      'root = Card([c])\nc = BarChart(["P1", "P2"], [Series("Low", [10, 15]), Series("High", [20, 25])], "grouped", "Period", "Value")',
    );

    expect(barFills(html)).toEqual(["#10B981", "#0284C7", "#10B981", "#0284C7"]);
    expect(html).toContain('data-series-legend="Low"');
    expect(html).toContain('data-series-legend="High"');
    expect(html).toContain('aria-pressed="true"');

    const hidden = toggleSeriesVisibility(new Set(), "Low", ["Low", "High"]);
    expect(hidden.has("Low")).toBe(true);
    expect(toggleSeriesVisibility(hidden, "Low", ["Low", "High"]).has("Low")).toBe(false);
    expect(toggleSeriesVisibility(new Set(), "Only", ["Only"]).size).toBe(0);
  });

  it("stacks multi-series bars while preserving series colors", () => {
    const html = render(
      'root = Card([c])\nc = BarChart(["P1", "P2"], [Series("Low", [10, 15]), Series("High", [20, 25])], "stacked", "Period", "Value")',
    );

    expect(barFills(html)).toEqual(["#10B981", "#0284C7", "#10B981", "#0284C7"]);
    expect(html).toContain('data-bar-series="Low"');
    expect(html).toContain('data-bar-series="High"');
  });

  it("draws positive and negative bars around a zero baseline", () => {
    const html = render(
      'root = Card([c])\nc = BarChart(["Loss", "Gain"], [Series("Return", [-10, 20])], "grouped", "Period", "Return (%)")',
    );

    expect(html).toContain("portfolio-chart__zero");
    expect(html).toContain('data-bar-value="-10"');
    expect(html).toContain('data-bar-value="20"');
    expect(barFills(html)).toHaveLength(2);
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
