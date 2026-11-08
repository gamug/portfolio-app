import { createRoot } from "react-dom/client";
import { Renderer } from "@openuidev/react-lang";
import { openuiLibrary } from "@openuidev/react-ui/genui-lib";
import "@openuidev/react-ui/styles/index.css";
import "./export.css";

type ReportMeta = {
  title?: unknown;
  date?: unknown;
};

const rootElement = document.getElementById("root");
if (rootElement === null) {
  throw new Error("missing root element");
}

const metaElement = document.getElementById("report-meta");
const dataElement = document.getElementById("report-data");
const meta = JSON.parse(metaElement?.textContent ?? "{}") as ReportMeta;
const report = JSON.parse(dataElement?.textContent ?? '""') as unknown;
const title =
  typeof meta.title === "string" && meta.title.trim().length > 0 ? meta.title : "Report";
const date = typeof meta.date === "string" ? meta.date : "";
const openuiLang = typeof report === "string" ? report : "";

document.title = title;

createRoot(rootElement).render(
  <main className="export-shell">
    <header className="export-header">
      <h1>{title}</h1>
      {date.length > 0 ? <p className="export-date">{date}</p> : null}
    </header>
    <div className="export-report">
      <Renderer response={openuiLang} library={openuiLibrary} />
    </div>
  </main>,
);
