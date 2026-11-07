import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@openuidev/react-ui/styles/index.css";
import { App } from "./App";
import "./styles.css";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("missing root element");
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
