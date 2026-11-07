import { useState } from "react";
import { applyTheme, readTheme, saveTheme, type Theme } from "./theme";

function asTheme(value: string): Theme {
  return value === "light" || value === "dark" ? value : "system";
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(readTheme);

  const change = (value: string) => {
    const next = asTheme(value);
    setTheme(next);
    applyTheme(next);
    saveTheme(next);
  };

  return (
    <label className="theme-toggle">
      <span>Theme</span>
      <select aria-label="Theme" value={theme} onChange={(event) => change(event.target.value)}>
        <option value="system">System</option>
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
    </label>
  );
}
