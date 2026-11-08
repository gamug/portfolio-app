#!/usr/bin/env node
/* global Buffer, console */
// Builds the offline report template from frontend/report-export.
// The template keeps the report data and metadata as JSON placeholders; the
// browser fills them at download time. Every script and stylesheet is inlined.
import { mkdtempSync, mkdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { build } from "vite";

const here = dirname(fileURLToPath(import.meta.url));
const frontend = resolve(here, "..");
const entry = resolve(frontend, "report-export");
const publicDir = resolve(frontend, "public");
const output = resolve(publicDir, "report-template.html");
const temporary = mkdtempSync(join(tmpdir(), "portfolio-report-template-"));
const built = join(temporary, "build");

function assetPath(url) {
  return resolve(built, url.replace(/^\//, ""));
}

// Keep this check in sync with hasExternalReferences in
// frontend/src/sessions/reportExport.ts: it must reject real resources but
// ignore URLs that are only documentation text inside the bundled JavaScript.
function withoutScriptContents(html) {
  return html.replace(/(<script\b[^>]*>)[\s\S]*?<\/script>/gi, "$1");
}

function withoutInlineCodeContents(html) {
  return withoutScriptContents(html).replace(/(<style\b[^>]*>)[\s\S]*?<\/style>/gi, "$1");
}

function hasExternalCssUrl(css) {
  return /(?<![A-Za-z0-9_])url\(\s*["']?(?:https?:)?\/\//i.test(css);
}

function hasExternalReferences(html) {
  const shell = withoutInlineCodeContents(html);
  if (/<[a-z][^>]*(?<![\w-])(?:src|href)\s*=\s*["'](?:https?:)?\/\//i.test(shell)) {
    return true;
  }
  const styleAttributes = [...shell.matchAll(/(?<![\w-])style\s*=\s*["']([^"']*)["']/gi)].map(
    (match) => match[1] ?? "",
  );
  const styleBlocks = [
    ...withoutScriptContents(html).matchAll(/<style\b[^>]*>([\s\S]*?)<\/style>/gi),
  ].map((match) => match[1] ?? "");
  return [...styleAttributes, ...styleBlocks].some(hasExternalCssUrl);
}

function inlineHtml() {
  let html = readFileSync(join(built, "index.html"), "utf8");
  html = html.replace(/<link\b(?=[^>]*rel="modulepreload")[^>]*>/g, "");

  let javascriptBytes = 0;
  html = html.replace(/<script\b(?=[^>]*src="([^"]+)")[^>]*><\/script>/g, (_, source) => {
    const javascript = readFileSync(assetPath(source), "utf8").replace(/<\/script/gi, "<\\/script");
    javascriptBytes += Buffer.byteLength(javascript);
    return `<script type="module">\n${javascript}\n</script>`;
  });

  let cssBytes = 0;
  html = html.replace(
    /<link\b(?=[^>]*rel="stylesheet")(?=[^>]*href="([^"]+)")[^>]*>/g,
    (_, href) => {
      const css = readFileSync(assetPath(href), "utf8").replace(/<\/style/gi, "<\\/style");
      cssBytes += Buffer.byteLength(css);
      return `<style>\n${css}\n</style>`;
    },
  );

  for (const placeholder of ["__REPORT_META__", "__REPORT_DATA__"]) {
    if (!html.includes(placeholder)) {
      throw new Error(`The report template is missing ${placeholder}.`);
    }
  }

  if (hasExternalReferences(html)) {
    throw new Error("The report template has external references.");
  }

  return { html, javascriptBytes, cssBytes };
}

try {
  await build({
    root: entry,
    configFile: false,
    plugins: [react()],
    build: {
      outDir: built,
      emptyOutDir: true,
      assetsInlineLimit: 100_000_000,
      chunkSizeWarningLimit: 5000,
      rollupOptions: {
        output: {
          inlineDynamicImports: true,
        },
      },
    },
  });

  const { html, javascriptBytes, cssBytes } = inlineHtml();
  mkdirSync(publicDir, { recursive: true });
  writeFileSync(output, html, "utf8");
  const bytes = statSync(output).size;
  console.log(
    `report template: ${bytes} bytes; inlined js ${javascriptBytes}; inlined css ${cssBytes}; ` +
      "external references 0",
  );
} finally {
  rmSync(temporary, { recursive: true, force: true });
}
