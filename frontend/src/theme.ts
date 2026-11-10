import { useCallback, useSyncExternalStore } from "react";
import { createTheme } from "@openuidev/react-ui";

export type Theme = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

const STORAGE_KEY = "portfolio-theme";
const DARK_QUERY = "(prefers-color-scheme: dark)";
const themeListeners = new Set<() => void>();
let appliedTheme: Theme | null = null;

const DARK_CHART_PALETTE = ["#FB7185", "#34D399", "#60A5FA", "#A78BFA", "#FBBF24"];
const LIGHT_CHART_PALETTE = ["#E11D48", "#10B981", "#2563EB", "#7C3AED", "#D97706"];

const DARK_SEMANTIC_TOKENS = {
  foreground: "oklch(0.21 0.028 265)",
  textNeutralPrimary: "oklch(0.93 0.012 255)",
  textNeutralSecondary: "oklch(0.72 0.02 255)",
  textNeutralTertiary: "oklch(0.58 0.02 255)",
  background: "oklch(0.17 0.025 265)",
  sunk: "oklch(0.21 0.028 265)",
  sunkDeep: "oklch(0.16 0.025 265)",
  elevated: "oklch(0.25 0.032 265)",
  elevatedLight: "oklch(0.23 0.03 265)",
  popoverBackground: "oklch(0.25 0.032 265)",
  borderDefault: "oklch(0.3 0.032 260)",
  interactiveAccentDefault: "oklch(0.62 0.19 258)",
  interactiveDestructiveDefault: "oklch(0.6 0.18 25)",
  textSuccessPrimary: "oklch(0.79 0.14 165)",
  successBackground: "oklch(0.31 0.055 165)",
  borderSuccess: "oklch(0.5 0.09 165)",
  textDangerPrimary: "oklch(0.72 0.16 25)",
  dangerBackground: "oklch(0.3 0.07 25)",
  borderDanger: "oklch(0.5 0.1 25)",
  textAlertPrimary: "oklch(0.84 0.16 85)",
  alertBackground: "oklch(0.32 0.055 85)",
  borderAlert: "oklch(0.5 0.09 85)",
  borderAlertEmphasis: "oklch(0.64 0.13 85)",
} as const;

const LIGHT_SEMANTIC_TOKENS = {
  foreground: "oklch(1 0 0)",
  textNeutralPrimary: "oklch(0.21 0.03 260)",
  textNeutralSecondary: "oklch(0.48 0.02 255)",
  textNeutralTertiary: "oklch(0.62 0.02 255)",
  background: "oklch(0.97 0.006 250)",
  sunk: "oklch(0.985 0.004 250)",
  sunkDeep: "oklch(0.94 0.01 250)",
  elevated: "oklch(1 0 0)",
  elevatedLight: "oklch(0.995 0.002 250)",
  popoverBackground: "oklch(1 0 0)",
  borderDefault: "oklch(0.92 0.012 250)",
  interactiveAccentDefault: "oklch(0.55 0.22 260)",
  interactiveDestructiveDefault: "oklch(0.55 0.2 27)",
  textSuccessPrimary: "oklch(0.52 0.12 160)",
  successBackground: "oklch(0.96 0.03 165)",
  borderSuccess: "oklch(0.82 0.08 165)",
  textDangerPrimary: "oklch(0.51 0.19 27)",
  dangerBackground: "oklch(0.96 0.03 25)",
  borderDanger: "oklch(0.84 0.08 25)",
  textAlertPrimary: "oklch(0.55 0.14 70)",
  alertBackground: "oklch(0.97 0.04 85)",
  borderAlert: "oklch(0.86 0.08 80)",
  borderAlertEmphasis: "oklch(0.72 0.12 75)",
} as const;

function chartPalette(palette: string[]) {
  return {
    defaultChartPalette: palette,
    barChartPalette: palette,
    lineChartPalette: palette,
    areaChartPalette: palette,
    pieChartPalette: palette,
    radarChartPalette: palette,
    radialChartPalette: palette,
    horizontalBarChartPalette: palette,
  };
}

export const portfolioLightTheme = createTheme({
  ...chartPalette(LIGHT_CHART_PALETTE),
  ...LIGHT_SEMANTIC_TOKENS,
});

export const portfolioDarkTheme = createTheme({
  ...chartPalette(DARK_CHART_PALETTE),
  ...DARK_SEMANTIC_TOKENS,
});

export function readTheme(): Theme {
  try {
    const value = globalThis.localStorage?.getItem(STORAGE_KEY);
    if (value === "light" || value === "dark" || value === "system") {
      return value;
    }
  } catch {
    // Private browsing or a blocked storage API: fall back to the system setting.
  }
  return "system";
}

export function applyTheme(theme: Theme): void {
  appliedTheme = theme;
  if (typeof document !== "undefined") {
    const root = document.documentElement;
    if (theme === "system") {
      root.removeAttribute("data-theme");
      root.removeAttribute("data-openui-theme");
    } else {
      root.dataset.theme = theme;
      root.dataset.openuiTheme = theme;
    }
  }
  for (const listener of themeListeners) {
    listener();
  }
}

export function saveTheme(theme: Theme): void {
  try {
    globalThis.localStorage?.setItem(STORAGE_KEY, theme);
  } catch {
    // The current choice still applies for this page; the next load uses the system value.
  }
}

export function subscribeTheme(listener: () => void): () => void {
  themeListeners.add(listener);
  return () => {
    themeListeners.delete(listener);
  };
}

function currentTheme(): Theme {
  if (appliedTheme !== null) {
    return appliedTheme;
  }
  if (typeof document !== "undefined") {
    const value = document.documentElement?.dataset?.theme;
    if (value === "light" || value === "dark") {
      return value;
    }
  }
  return "system";
}

function systemPrefersDark(): boolean {
  try {
    if (typeof globalThis.matchMedia !== "function") {
      return false;
    }
    return globalThis.matchMedia(DARK_QUERY).matches;
  } catch {
    return false;
  }
}

export function resolveThemeMode(theme: Theme): ResolvedTheme {
  if (theme !== "system") {
    return theme;
  }
  return systemPrefersDark() ? "dark" : "light";
}

export function useResolvedThemeMode(): ResolvedTheme {
  const subscribe = useCallback((listener: () => void) => {
    const unsubscribe = subscribeTheme(listener);
    if (typeof globalThis.matchMedia !== "function") {
      return unsubscribe;
    }
    const query = globalThis.matchMedia(DARK_QUERY);
    query.addEventListener("change", listener);
    return () => {
      query.removeEventListener("change", listener);
      unsubscribe();
    };
  }, []);

  return useSyncExternalStore(
    subscribe,
    () => resolveThemeMode(currentTheme()),
    () => "light",
  );
}
