import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ThemeToggle } from "./ThemeToggle";
import { applyTheme, readTheme, saveTheme } from "./theme";

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
});
