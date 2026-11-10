"""Second DeepSeek call that converts a completed answer to OpenUI Lang."""

import time
from pathlib import Path
from typing import Any

from openai import APITimeoutError, AsyncOpenAI

from .language import Language, conversion_instruction
from .models import ConnectorError, ConnectorTimeout, ConversionResult, total_tokens
from .settings import Settings

CONVERSION_TASK = """Convert the answer text into a short OpenUI Lang chat response
using the chat component library. The answer text is the only source of facts.

Hard limits:
- Keep it to at most 6 statements in total, including root. Each statement is one assignment.
  Use only Card, CardHeader, TextContent and, only when required, one chart (BarChart,
  HorizontalBarChart, LineChart, AreaChart or PieChart) or one Table with their labels and
  series. Inline short arrays instead of defining extra variables.
- Do not use FollowUpBlock, FollowUpItem, CodeBlock, EntityList, nested card blocks, forms,
  sections or carousels in this short conversion.
- Do not invent facts, numbers, categories or labels beyond the answer text. Return only
  OpenUI Lang, without markdown fences.

Visible text rules:
- Never emit a loose label, a bare type name such as "number" or "text", a field or column name,
  or a heading or title without content as visible text. Omit headings and labels that have no
  content under them, and do not render empty text components.
- Show only the analyst-facing answer. Do not include raw queries, code blocks, tool metadata or
  process notes.
- Keep TextContent concise: a 1-2 sentence key takeaway with explicit "+" or "-" signs on
  returns and deltas when the answer supports them, rather than repeating the entire raw answer
  table.

Chart rules:
- Add a chart only when the answer contains a table with at least two numeric values over
  categories. In that case the chart is mandatory: include exactly one chart for that table and
  do not replace it with a Table alone.
- Choose the visual type from the table's data:
  - LineChart(..., "natural", xLabel, yLabel) for time series, NAV evolution, or multi-date
    trajectories.
  - AreaChart(..., "natural", xLabel, yLabel) for cumulative value or volume over time.
  - HorizontalBarChart for ranked lists, performance rankings, or long category/strategy names.
  - PieChart(labels, values, "donut") for portfolio weights or non-negative shares of a whole.
  - BarChart only for short-label categorical comparisons; do not default to vertical BarChart
    for time series or long strategy names.
- Pass concise, real axis labels (xLabel, yLabel) from the table headers or units instead of the
  literal "Category" or "Value".
- Use only that table's categories and numbers.
- If the answer has no such table, do not add any chart, even when the answer contains numbers.
  These chart rules override any general chart guidance in the component reference."""
DEFAULT_PROMPT_PATH = Path(__file__).with_name("openui_chat_prompt.txt")


class OpenUIConverter:
    """Convert the final answer with one additional DeepSeek call; no retries."""

    def __init__(
        self,
        settings: Settings,
        llm: Any = None,
        prompt_path: Path | None = None,
    ) -> None:
        self.settings = settings
        self.prompt_path = prompt_path or DEFAULT_PROMPT_PATH
        self.llm: Any = llm or AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_url,
            timeout=settings.chat_timeout_seconds,
            max_retries=0,
        )

    async def convert(self, answer: str, language: Language = "en") -> ConversionResult:
        started = time.monotonic()
        try:
            prompt = self.prompt_path.read_text(encoding="utf-8")
        except OSError as error:
            raise ConnectorError(
                "The OpenUI conversion prompt is missing.",
                status_code=502,
                kind="conversion",
            ) from error
        try:
            response = await self.llm.chat.completions.create(
                model=self.settings.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"{prompt}\n\n{CONVERSION_TASK}\n\n{conversion_instruction(language)}"
                        ),
                    },
                    {"role": "user", "content": answer},
                ],
                temperature=0,
                max_tokens=1500,
                timeout=self.settings.chat_timeout_seconds,
            )
        except APITimeoutError as error:
            raise ConnectorTimeout(
                f"The OpenUI conversion timed out after {self.settings.chat_timeout_seconds:g} s."
            ) from error
        except Exception as error:  # noqa: BLE001 - convert provider failures
            raise ConnectorError(
                "The OpenUI conversion failed.", status_code=502, kind="deepseek"
            ) from error

        content = response.choices[0].message.content or ""
        converted = _strip_fences(content)
        if not converted:
            raise ConnectorError(
                "The OpenUI conversion returned an empty response.",
                status_code=502,
                kind="conversion",
            )
        usage = response.usage.model_dump() if response.usage else None
        return ConversionResult(
            text=converted,
            latency_seconds=round(time.monotonic() - started, 3),
            usage=usage,
            total_tokens=total_tokens(usage),
        )


def _strip_fences(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()
