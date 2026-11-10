import { renderToStaticMarkup } from "react-dom/server";
import { Renderer } from "@openuidev/react-lang";
import { openuiLibrary, ThemeProvider } from "@openuidev/react-ui";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ThemeToggle } from "./ThemeToggle";
import {
  applyTheme,
  portfolioDarkTheme,
  portfolioLightTheme,
  readTheme,
  resolveThemeMode,
  saveTheme,
  subscribeTheme,
} from "./theme";

afterEach(() => {
  vi.unstubAllGlobals();
});

function storage(initial: Record<string, string> = {}) {
  const values = new Map(Object.entries(initial));
  return {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => {
      values.set(key, value);
    },
    removeItem: (key: string) => {
      values.delete(key);
    },
    clear: () => {
      values.clear();
    },
    key: () => null,
    length: 0,
  };
}

describe("theme", () => {
  it("renders the system, light and dark choices", () => {
    const html = renderToStaticMarkup(<ThemeToggle />);
    expect(html).toContain('aria-label="Theme"');
    expect(html).toContain('value="system"');
    expect(html).toContain('value="light"');
    expect(html).toContain('value="dark"');
  });

  it("applies an explicit theme to the app and the OpenUI library", () => {
    const root = { dataset: {} as Record<string, string>, removeAttribute: vi.fn() };
    vi.stubGlobal("document", { documentElement: root });

    applyTheme("dark");
    expect(root.dataset).toEqual({ theme: "dark", openuiTheme: "dark" });

    applyTheme("light");
    expect(root.dataset).toEqual({ theme: "light", openuiTheme: "light" });

    applyTheme("system");
    expect(root.removeAttribute).toHaveBeenCalledWith("data-theme");
    expect(root.removeAttribute).toHaveBeenCalledWith("data-openui-theme");
  });

  it("remembers the choice and falls back to system", () => {
    const local = storage();
    vi.stubGlobal("localStorage", local);

    saveTheme("dark");
    expect(readTheme()).toBe("dark");

    saveTheme("light");
    expect(readTheme()).toBe("light");

    local.clear();
    expect(readTheme()).toBe("system");
  });

  it("ignores an unknown stored value", () => {
    vi.stubGlobal("localStorage", storage({ "portfolio-theme": "sepia" }));
    expect(readTheme()).toBe("system");
  });

  it("notifies subscribers when the applied theme changes", () => {
    const root = { dataset: {} as Record<string, string>, removeAttribute: vi.fn() };
    vi.stubGlobal("document", { documentElement: root });
    const listener = vi.fn();
    const unsubscribe = subscribeTheme(listener);

    applyTheme("dark");
    expect(listener).toHaveBeenCalledTimes(1);

    unsubscribe();
    applyTheme("light");
    expect(listener).toHaveBeenCalledTimes(1);
  });

  it("resolves the effective mode from an explicit theme or the system preference", () => {
    expect(resolveThemeMode("light")).toBe("light");
    expect(resolveThemeMode("dark")).toBe("dark");
    expect(resolveThemeMode("system")).toBe("light");

    vi.stubGlobal(
      "matchMedia",
      vi.fn(() => ({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() })),
    );
    expect(resolveThemeMode("system")).toBe("dark");
  });

  it("defines five categorical colours and semantic tokens in both modes", () => {
    const paletteKeys = [
      "defaultChartPalette",
      "barChartPalette",
      "lineChartPalette",
      "areaChartPalette",
      "pieChartPalette",
      "radarChartPalette",
      "radialChartPalette",
      "horizontalBarChartPalette",
    ] as const;
    const tokenKeys = [
      "foreground",
      "background",
      "sunk",
      "elevated",
      "borderDefault",
      "interactiveAccentDefault",
      "textSuccessPrimary",
      "successBackground",
      "textDangerPrimary",
      "dangerBackground",
      "textAlertPrimary",
      "alertBackground",
      "borderAlert",
      "borderAlertEmphasis",
    ] as const;

    for (const theme of [portfolioLightTheme, portfolioDarkTheme]) {
      for (const key of paletteKeys) {
        expect(theme[key]).toHaveLength(5);
      }
      for (const key of tokenKeys) {
        expect(theme[key]).toMatch(/^oklch\(/);
      }
    }

    expect(portfolioDarkTheme.defaultChartPalette).toEqual([
      "#FB7185",
      "#34D399",
      "#60A5FA",
      "#A78BFA",
      "#FBBF24",
    ]);
    expect(portfolioLightTheme.defaultChartPalette).toEqual([
      "#E11D48",
      "#10B981",
      "#2563EB",
      "#7C3AED",
      "#D97706",
    ]);
  });

  it("uses surface colours for the openui foreground token", () => {
    expect(portfolioDarkTheme.foreground).not.toBe(portfolioDarkTheme.textNeutralPrimary);
    expect(portfolioLightTheme.foreground).not.toBe(portfolioLightTheme.textNeutralPrimary);
  });

  it("provides the portfolio chart palette to the OpenUI library", () => {
    const html = renderToStaticMarkup(
      <ThemeProvider mode="dark" lightTheme={portfolioLightTheme} darkTheme={portfolioDarkTheme}>
        <Renderer
          response={
            'root = Card([c])\nc = BarChart(["A", "B"], [Series("S1", [1, 2]), Series("S2", [3, 4])])'
          }
          library={openuiLibrary}
        />
      </ThemeProvider>,
    );

    expect(html).toContain("#34D399");
    expect(html).toContain("#A78BFA");
    expect(html).not.toContain("#1E88E5");
    expect(html).not.toContain("#42A5F5");
  });
});
