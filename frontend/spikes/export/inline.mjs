import { Buffer } from "node:buffer";
import { readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const dist = resolve(here, "../../../backend/tests/evaluation/local-results/task-019-export");
const indexPath = resolve(dist, "index.html");

function assetPath(url) {
  return resolve(dist, url.replace(/^\//, ""));
}

let html = readFileSync(indexPath, "utf-8");
html = html.replace(/<link\b(?=[^>]*rel="modulepreload")[^>]*>/g, "");

let jsBytes = 0;
html = html.replace(/<script\b(?=[^>]*src="([^"]+)")[^>]*><\/script>/g, (_, source) => {
  const javascript = readFileSync(assetPath(source), "utf-8").replace(/<\/script/gi, "<\\/script");
  jsBytes += Buffer.byteLength(javascript);
  return `<script type="module">\n${javascript}\n</script>`;
});

let cssBytes = 0;
html = html.replace(/<link\b(?=[^>]*rel="stylesheet")(?=[^>]*href="([^"]+)")[^>]*>/g, (_, href) => {
  const css = readFileSync(assetPath(href), "utf-8").replace(/<\/style/gi, "<\\/style");
  cssBytes += Buffer.byteLength(css);
  return `<style>\n${css}\n</style>`;
});

const attributeUrls = [...html.matchAll(/(?:src|href)=["'](https?:\/\/[^"']+)/g)].map(
  (match) => match[1],
);
const cssUrls = [...html.matchAll(/url\(\s*["']?(https?:\/\/[^"')\s]+)/g)].map((match) => match[1]);
const externalReferences = [...attributeUrls, ...cssUrls];
const reportPath = resolve(dist, "report.html");
writeFileSync(reportPath, html, "utf-8");
const metadata = {
  report_bytes: statSync(reportPath).size,
  inlined_javascript_bytes: jsBytes,
  inlined_css_bytes: cssBytes,
  external_references: externalReferences,
};
writeFileSync(
  resolve(dist, "task-019-export.json"),
  `${JSON.stringify(metadata, null, 2)}\n`,
  "utf-8",
);
process.stdout.write(
  `report.html: ${metadata.report_bytes} bytes; js: ${jsBytes}; css: ${cssBytes}; ` +
    `external references: ${externalReferences.length}\n`,
);
if (externalReferences.length > 0) {
  process.exitCode = 1;
}
