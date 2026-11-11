#!/usr/bin/env node
/* global Buffer, process */
// Validate one OpenUI Lang report with the same parser the TASK-019 spike used.
// Reads the program from stdin and writes one JSON result to stdout. Exit code 0 means valid.
import { createParser } from "@openuidev/react-lang";
// portfolioReportLibrary extends this library with renderer-only overrides, so
// the schema used for validation is identical for both.
import { openuiLibrary } from "@openuidev/react-ui";

const chunks = [];
for await (const chunk of process.stdin) {
  chunks.push(chunk);
}
const text = Buffer.concat(chunks).toString("utf8");

let payload;
try {
  const result = createParser(openuiLibrary.toJSONSchema(), openuiLibrary.root).parse(text);
  payload = {
    parsed: true,
    root_present: result.root !== null,
    errors: result.meta.errors.length,
    unresolved: result.meta.unresolved.length,
    orphaned: result.meta.orphaned.length,
    incomplete: result.meta.incomplete,
    statements: result.meta.statementCount,
  };
} catch (error) {
  payload = {
    parsed: false,
    root_present: false,
    errors: 1,
    unresolved: 1,
    orphaned: 0,
    incomplete: true,
    statements: 0,
    error: String(error),
  };
}

process.stdout.write(JSON.stringify(payload));
const valid =
  payload.parsed &&
  payload.root_present &&
  payload.errors === 0 &&
  payload.unresolved === 0 &&
  payload.orphaned === 0 &&
  payload.incomplete === false;
process.exitCode = valid ? 0 : 1;
