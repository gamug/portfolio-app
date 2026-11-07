import { createRoot } from "react-dom/client";
import { Renderer } from "@openuidev/react-lang";
import { openuiLibrary } from "@openuidev/react-ui/genui-lib";
import "@openuidev/react-ui/styles/index.css";
import report from "./sample-report.openui?raw";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("missing root element");
}

createRoot(rootElement).render(<Renderer response={report} library={openuiLibrary} />);
