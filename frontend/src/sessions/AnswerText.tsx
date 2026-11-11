import { Fragment, type ReactNode } from "react";

type AnswerTextProps = {
  text: string;
};

const INLINE_PATTERN = /(\*\*(?:[^*]|\*(?!\*))+\*\*|`[^`]+`|(?<!\*)\*(?!\*)[^*]+\*)/g;
const BULLET_PATTERN = /^\s*[-*+]\s+(.*)$/;
const ORDERED_PATTERN = /^\s*\d+[.)]\s+(.*)$/;
const HEADING_PATTERN = /^(#{1,6})\s+(.*)$/;
const TABLE_DIVIDER_PATTERN = /^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$/;

export function renderMetrics(text: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const pattern = /(^|[\s(])([+-]\$?\d[\d,]*(?:\.\d+)?%?)/g;
  let lastIndex = 0;
  let match = pattern.exec(text);

  while (match !== null) {
    const boundary = match[1] ?? "";
    const metric = match[2];
    if (metric === undefined) {
      match = pattern.exec(text);
      continue;
    }
    const start = match.index + boundary.length;
    if (start > lastIndex) {
      nodes.push(text.slice(lastIndex, start));
    }
    const direction = metric.startsWith("+") ? "positive" : "negative";
    nodes.push(
      <span
        key={`metric-${start}`}
        className={`answer-text__metric answer-text__metric--${direction}`}
      >
        {metric}
      </span>,
    );
    lastIndex = start + metric.length;
    match = pattern.exec(text);
  }

  if (lastIndex < text.length) {
    nodes.push(text.slice(lastIndex));
  }
  return nodes;
}

export function renderInline(text: string): ReactNode[] {
  return text.split(INLINE_PATTERN).map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      return <strong key={index}>{renderInline(part.slice(2, -2))}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`") && part.length > 2) {
      return <code key={index}>{part.slice(1, -1)}</code>;
    }
    if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
      return <em key={index}>{part.slice(1, -1)}</em>;
    }
    return <Fragment key={index}>{renderMetrics(part)}</Fragment>;
  });
}

function tableCells(line: string): string[] {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

function isBlockStart(line: string): boolean {
  return (
    line.trim().length === 0 ||
    HEADING_PATTERN.test(line) ||
    BULLET_PATTERN.test(line) ||
    ORDERED_PATTERN.test(line) ||
    line.includes("|")
  );
}

function renderBlocks(text: string): ReactNode[] {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let index = 0;
  let key = 0;

  while (index < lines.length) {
    const line = lines[index] ?? "";
    if (line.trim().length === 0) {
      index += 1;
      continue;
    }

    const heading = HEADING_PATTERN.exec(line);
    if (heading !== null) {
      blocks.push(<h4 key={key}>{renderInline(heading[2] ?? "")}</h4>);
      key += 1;
      index += 1;
      continue;
    }

    if (
      line.includes("|") &&
      index + 1 < lines.length &&
      TABLE_DIVIDER_PATTERN.test(lines[index + 1] ?? "")
    ) {
      const header = tableCells(line);
      const rows: string[][] = [];
      index += 2;
      while (index < lines.length && (lines[index] ?? "").includes("|")) {
        rows.push(tableCells(lines[index] ?? ""));
        index += 1;
      }
      blocks.push(
        <div className="answer-text__table-wrap" key={key}>
          <table>
            <thead>
              <tr>
                {header.map((cell, cellIndex) => (
                  <th key={cellIndex} scope="col">
                    {renderInline(cell)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {header.map((_, cellIndex) => (
                    <td key={cellIndex}>{renderInline(row[cellIndex] ?? "")}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      key += 1;
      continue;
    }

    const bullet = BULLET_PATTERN.exec(line);
    if (bullet !== null) {
      const items: string[] = [];
      while (index < lines.length) {
        const item = BULLET_PATTERN.exec(lines[index] ?? "");
        if (item === null) {
          break;
        }
        items.push(item[1] ?? "");
        index += 1;
      }
      blocks.push(
        <ul key={key}>
          {items.map((item, itemIndex) => (
            <li key={itemIndex}>{renderInline(item)}</li>
          ))}
        </ul>,
      );
      key += 1;
      continue;
    }

    const ordered = ORDERED_PATTERN.exec(line);
    if (ordered !== null) {
      const items: string[] = [];
      while (index < lines.length) {
        const item = ORDERED_PATTERN.exec(lines[index] ?? "");
        if (item === null) {
          break;
        }
        items.push(item[1] ?? "");
        index += 1;
      }
      blocks.push(
        <ol key={key}>
          {items.map((item, itemIndex) => (
            <li key={itemIndex}>{renderInline(item)}</li>
          ))}
        </ol>,
      );
      key += 1;
      continue;
    }

    const paragraph: string[] = [line];
    index += 1;
    while (index < lines.length && !isBlockStart(lines[index] ?? "")) {
      paragraph.push(lines[index] ?? "");
      index += 1;
    }
    blocks.push(<p key={key}>{renderInline(paragraph.join("\n"))}</p>);
    key += 1;
  }

  return blocks;
}

export function AnswerText({ text }: AnswerTextProps) {
  return <div className="answer-text">{renderBlocks(text)}</div>;
}
