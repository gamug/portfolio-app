export type Theme = "light" | "dark" | "system";

const STORAGE_KEY = "portfolio-theme";

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
  if (typeof document === "undefined") {
    return;
  }
  const root = document.documentElement;
  if (theme === "system") {
    root.removeAttribute("data-theme");
    root.removeAttribute("data-openui-theme");
    return;
  }
  root.dataset.theme = theme;
  root.dataset.openuiTheme = theme;
}

export function saveTheme(theme: Theme): void {
  try {
    globalThis.localStorage?.setItem(STORAGE_KEY, theme);
  } catch {
    // The current choice still applies for this page; the next load uses the system value.
  }
}
