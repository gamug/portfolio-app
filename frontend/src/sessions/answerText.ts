import type { Message } from "@openuidev/react-ui";

const TEXT_COMPONENTS = [
  "TextContent",
  "MarkDownRenderer",
  "CardHeader",
  "InlineHeader",
  "Text",
  "BoldText",
] as const;
type TextComponent = (typeof TEXT_COMPONENTS)[number];
const TEXT_COMPONENT_PATTERN = new RegExp(`\\b(${TEXT_COMPONENTS.join("|")})\\s*\\(`, "g");
const MULTI_STRING_COMPONENTS = new Set<TextComponent>(["CardHeader", "InlineHeader"]);

export function messageText(message: Message): string {
  return typeof message.content === "string" ? message.content : "";
}

export function extractAnswerText(openuiLang: string): string {
  const parts: string[] = [];
  for (const match of openuiLang.matchAll(TEXT_COMPONENT_PATTERN)) {
    const index = match.index;
    if (index === undefined) {
      continue;
    }
    const component = match[1] as TextComponent;
    const open = index + match[0].lastIndexOf("(");
    const close = findClosingParen(openuiLang, open);
    if (close === -1) {
      continue;
    }
    const args = splitTopLevelArgs(openuiLang.slice(open + 1, close));
    const strings = args
      .map((argument) => parseStringLiteral(argument))
      .filter((value): value is string => value !== null);
    if (MULTI_STRING_COMPONENTS.has(component)) {
      parts.push(...strings);
    } else if (strings[0] !== undefined) {
      parts.push(strings[0]);
    }
  }
  const seen = new Set<string>();
  return parts
    .map((part) => part.trim())
    .filter((part) => {
      if (part.length === 0 || seen.has(part)) {
        return false;
      }
      seen.add(part);
      return true;
    })
    .join("\n\n");
}

function findClosingParen(text: string, open: number): number {
  let depth = 1;
  let quote: string | null = null;
  let escaped = false;
  for (let index = open + 1; index < text.length; index += 1) {
    const character = text[index];
    if (character === undefined) {
      break;
    }
    if (quote !== null) {
      if (escaped) {
        escaped = false;
      } else if (character === "\\") {
        escaped = true;
      } else if (character === quote) {
        quote = null;
      }
      continue;
    }
    if (character === '"' || character === "'") {
      quote = character;
    } else if (character === "(") {
      depth += 1;
    } else if (character === ")") {
      depth -= 1;
      if (depth === 0) {
        return index;
      }
    }
  }
  return -1;
}

function splitTopLevelArgs(value: string): string[] {
  const args: string[] = [];
  let depth = 0;
  let quote: string | null = null;
  let escaped = false;
  let start = 0;
  for (let index = 0; index < value.length; index += 1) {
    const character = value[index];
    if (character === undefined) {
      break;
    }
    if (quote !== null) {
      if (escaped) {
        escaped = false;
      } else if (character === "\\") {
        escaped = true;
      } else if (character === quote) {
        quote = null;
      }
      continue;
    }
    if (character === '"' || character === "'") {
      quote = character;
    } else if (character === "(" || character === "[" || character === "{") {
      depth += 1;
    } else if (character === ")" || character === "]" || character === "}") {
      depth -= 1;
    } else if (character === "," && depth === 0) {
      args.push(value.slice(start, index).trim());
      start = index + 1;
    }
  }
  const last = value.slice(start).trim();
  if (last.length > 0) {
    args.push(last);
  }
  return args;
}

function parseStringLiteral(argument: string): string | null {
  const trimmed = argument.trim();
  const quote = trimmed[0];
  if (quote !== '"' && quote !== "'") {
    return null;
  }
  let value = "";
  let escaped = false;
  for (let index = 1; index < trimmed.length; index += 1) {
    const character = trimmed[index];
    if (character === undefined) {
      break;
    }
    if (escaped) {
      value += unescapeCharacter(character);
      escaped = false;
    } else if (character === "\\") {
      escaped = true;
    } else if (character === quote) {
      return value;
    } else {
      value += character;
    }
  }
  return value;
}

function unescapeCharacter(character: string): string {
  if (character === "n") {
    return "\n";
  }
  if (character === "r") {
    return "\r";
  }
  if (character === "t") {
    return "\t";
  }
  return character;
}
