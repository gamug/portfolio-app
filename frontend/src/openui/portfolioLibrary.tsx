import { useId, useState, type CSSProperties, type ReactNode } from "react";
import { defineComponent, useIsQueryLoading } from "@openuidev/react-lang";
import {
  openuiChatLibrary,
  openuiLibrary,
  ScrollableTable,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TableSkeleton,
  useTheme,
} from "@openuidev/react-ui";
import { AnswerText, renderInline } from "../sessions/AnswerText";

type SchemaLibrary = {
  components: Record<string, { props: unknown }>;
};

function schemaOf(
  library: SchemaLibrary,
  name: string,
): Parameters<typeof defineComponent>[0]["props"] {
  return library.components[name]?.props as Parameters<typeof defineComponent>[0]["props"];
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function elementProps(value: unknown): Record<string, unknown> | null {
  if (!isRecord(value)) {
    return null;
  }
  if (isRecord(value.props)) {
    return value.props;
  }
  return value;
}

const BODY_SIZE_VARS = {
  small: "--openui-text-body-sm",
  default: "--openui-text-body-default",
  large: "--openui-text-body-lg",
  "small-heavy": "--openui-text-body-sm-heavy",
  "large-heavy": "--openui-text-body-lg-heavy",
} as const;

type TextSize = keyof typeof BODY_SIZE_VARS;

function PortfolioTextContent({ text, size }: { text: unknown; size?: unknown }) {
  const sizeKey: TextSize =
    typeof size === "string" && size in BODY_SIZE_VARS ? (size as TextSize) : "default";
  const variable = BODY_SIZE_VARS[sizeKey];
  const style =
    sizeKey === "default"
      ? undefined
      : ({
          "--openui-text-body-default": `var(${variable})`,
          "--openui-text-body-default-letter-spacing": `var(${variable}-letter-spacing)`,
        } as CSSProperties);

  return (
    <div style={style} data-report-text={sizeKey}>
      <AnswerText text={text == null ? "" : String(text)} />
    </div>
  );
}

function PortfolioInlineHeader({
  heading,
  description,
}: {
  heading?: unknown;
  description?: unknown;
}) {
  const headingText = heading == null ? "" : String(heading);
  const descriptionText = description == null ? "" : String(description);
  if (headingText.length === 0 && descriptionText.length === 0) {
    return null;
  }

  return (
    <div className="openui-inline-header" data-report-inline-header="true">
      {headingText.length > 0 && (
        <div className="openui-inline-header-heading">{renderInline(headingText)}</div>
      )}
      {descriptionText.length > 0 && (
        <div className="openui-inline-header-description">{renderInline(descriptionText)}</div>
      )}
    </div>
  );
}

const TABLE_PAGE_SIZE = 10;

type TableColumn = {
  label: string;
  data: unknown[];
};

function PortfolioTable({
  columns,
  renderNode,
}: {
  columns?: unknown;
  renderNode: (node: unknown) => ReactNode;
}) {
  const isLoading = useIsQueryLoading();
  const [page, setPage] = useState(0);
  const definitions: TableColumn[] = (Array.isArray(columns) ? columns : [])
    .map((column) => elementProps(column))
    .filter((column): column is Record<string, unknown> => column !== null)
    .map((column) => ({
      label: String(column.label ?? ""),
      data: Array.isArray(column.data) ? column.data : column.data == null ? [] : [column.data],
    }))
    .filter((column) => column.label.length > 0);
  const rowCount =
    definitions.length === 0 ? 0 : Math.max(...definitions.map((column) => column.data.length));

  if (isLoading && rowCount === 0) {
    return <TableSkeleton rows={5} columns={Math.max(definitions.length, 3)} />;
  }
  if (definitions.length === 0) {
    return null;
  }

  const totalPages = Math.ceil(rowCount / TABLE_PAGE_SIZE);
  const safePage = Math.min(page, Math.max(0, totalPages - 1));
  const startRow = safePage * TABLE_PAGE_SIZE;
  const visibleRows = Math.min(TABLE_PAGE_SIZE, rowCount - startRow);

  return (
    <div data-report-table="true">
      <ScrollableTable>
        <TableHeader>
          <TableRow>
            {definitions.map((column, index) => (
              <TableHead key={`${column.label}-${index}`}>{column.label}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {Array.from({ length: visibleRows }, (_, rowIndex) => {
            const actualRow = startRow + rowIndex;
            return (
              <TableRow key={actualRow}>
                {definitions.map((column, columnIndex) => {
                  const cell = column.data[actualRow];
                  return (
                    <TableCell key={columnIndex}>
                      {typeof cell === "object" && cell !== null
                        ? renderNode(cell)
                        : renderInline(String(cell ?? ""))}
                    </TableCell>
                  );
                })}
              </TableRow>
            );
          })}
        </TableBody>
      </ScrollableTable>
      {totalPages > 1 && (
        <div className="portfolio-table__pagination">
          <button
            type="button"
            aria-label="Previous page"
            disabled={safePage === 0}
            onClick={() => setPage(Math.max(0, safePage - 1))}
          >
            ‹
          </button>
          <span>
            {safePage + 1} / {totalPages}
          </span>
          <button
            type="button"
            aria-label="Next page"
            disabled={safePage >= totalPages - 1}
            onClick={() => setPage(Math.min(totalPages - 1, safePage + 1))}
          >
            ›
          </button>
        </div>
      )}
    </div>
  );
}

const DEFAULT_CHART_PALETTE = ["#34D399", "#38BDF8", "#A78BFA", "#FBBF24", "#F87171"];
const FALLBACK_LINE_PALETTE = ["#34D399", "#38BDF8", "#A78BFA", "#FBBF24", "#F87171"];
const FALLBACK_AREA_PALETTE = ["#34D399", "#38BDF8", "#A78BFA", "#FBBF24", "#F87171"];
const VIEW_WIDTH = 760;
const PLOT_LEFT = 68;
const PLOT_RIGHT = 24;
const PLOT_TOP = 20;
const PLOT_BOTTOM = 40;
const MIN_CHART_HEIGHT = 360;
const EXACT_FORMAT = new Intl.NumberFormat("en-US", { maximumFractionDigits: 4 });
const COMPACT_FORMAT = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1,
});
const DATE_PATTERN =
  /(?:\b(?:19|20)\d{2}\b|\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b|^\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|ene|abr|ago|dic))/i;

type ChartVariant = "linear" | "natural" | "step";
type ChartKind = "line" | "area";

type ChartSeriesData = {
  name: string;
  values: number[];
};

type ChartProps = {
  labels?: unknown;
  series?: unknown;
  variant?: unknown;
  xLabel?: unknown;
  yLabel?: unknown;
  height?: unknown;
};

type Point = {
  x: number;
  y: number;
};

type YAxis = {
  rawMin: number;
  rawMax: number;
  min: number;
  max: number;
  ticks: number[];
  decimals: number;
};

function decimalPlaces(value: number): number {
  const text = String(Math.abs(value));
  if (text.includes("e-")) {
    return Math.min(8, Number(text.split("e-")[1] ?? 0));
  }
  const fraction = text.split(".")[1];
  return fraction === undefined ? 0 : fraction.length;
}

function normalizeLabels(value: unknown): string[] {
  return Array.isArray(value) ? value.map((label) => String(label ?? "")) : [];
}

function normalizeSeries(value: unknown, labels: string[]): ChartSeriesData[] {
  const entries = Array.isArray(value) ? value : value == null ? [] : [value];
  return entries.flatMap((entry, index) => {
    const props = elementProps(entry);
    if (props === null) {
      return [];
    }
    const name =
      typeof props.category === "string" && props.category.trim().length > 0
        ? props.category.trim()
        : `Serie ${index + 1}`;
    const rawValues = Array.isArray(props.values) ? props.values : [];
    const values = labels.map((_, labelIndex) => {
      const candidate = rawValues[labelIndex];
      if (typeof candidate === "number") {
        return candidate;
      }
      if (typeof candidate === "string" && candidate.trim().length > 0) {
        return Number(candidate);
      }
      return Number.NaN;
    });
    if (!values.some((candidate) => Number.isFinite(candidate))) {
      return [];
    }
    return [{ name, values }];
  });
}

function buildYAxis(values: number[]): YAxis {
  const finite = values.filter((value) => Number.isFinite(value));
  const rawMin = finite.length > 0 ? Math.min(...finite) : 0;
  const rawMax = finite.length > 0 ? Math.max(...finite) : 1;
  const range = rawMax - rawMin;
  let min: number;
  let max: number;

  if (rawMin > 0 && rawMax > 0 && range / rawMax < 0.65) {
    const pad = Math.max(range * 0.14, 0.005);
    min = Math.max(0, rawMin - pad);
    max = rawMax + pad;
  } else if (rawMin >= 0) {
    const pad = Math.max(range * 0.08, rawMax * 0.02, 0.005);
    min = 0;
    max = rawMax + pad;
  } else {
    const pad = Math.max(range * 0.08, 0.005);
    min = rawMin - pad;
    max = rawMax + pad;
  }

  if (!Number.isFinite(min) || !Number.isFinite(max) || min === max) {
    min = Math.min(0, rawMin - 0.5);
    max = Math.max(1, rawMax + 0.5);
  }

  const decimals = Math.min(3, Math.max(2, ...finite.map((value) => decimalPlaces(value))));
  const roughStep = (max - min) / 5;
  const magnitude = 10 ** Math.floor(Math.log10(roughStep));
  const normalized = roughStep / magnitude;
  const nice =
    normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 2.5 ? 2.5 : normalized <= 5 ? 5 : 10;
  const step = nice * magnitude;
  const ticks: number[] = [];
  const start = Math.ceil((min - step * 1e-9) / step) * step;
  const end = Math.floor((max + step * 1e-9) / step) * step;
  for (let value = start; value <= end + step * 1e-9; value += step) {
    ticks.push(Number(value.toFixed(10)));
  }
  if (ticks.length < 4) {
    ticks.length = 0;
    for (let index = 0; index <= 5; index += 1) {
      ticks.push(Number((min + ((max - min) * index) / 5).toFixed(10)));
    }
  }

  return { rawMin, rawMax, min, max, ticks, decimals };
}

function formatExact(value: number): string {
  return EXACT_FORMAT.format(Object.is(value, -0) ? 0 : value);
}

function formatTick(value: number, decimals: number): string {
  const absolute = Math.abs(value);
  if (absolute >= 10000) {
    return COMPACT_FORMAT.format(value);
  }
  if (decimals === 0 && absolute >= 1000) {
    return EXACT_FORMAT.format(value);
  }
  return (Object.is(value, -0) ? 0 : value).toFixed(decimals);
}

function readVariant(value: unknown): ChartVariant {
  return value === "linear" || value === "step" || value === "natural" ? value : "natural";
}

function readHeight(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value)
    ? Math.max(MIN_CHART_HEIGHT, Math.round(value))
    : MIN_CHART_HEIGHT;
}

function buildLinePath(points: Point[], variant: ChartVariant): string {
  if (points.length === 0) {
    return "";
  }
  const first = points[0];
  if (first === undefined) {
    return "";
  }
  if (points.length === 1) {
    return `M ${first.x} ${first.y}`;
  }
  if (variant === "step") {
    let path = `M ${first.x} ${first.y}`;
    for (let index = 1; index < points.length; index += 1) {
      const point = points[index];
      if (point !== undefined) {
        path += ` H ${point.x} V ${point.y}`;
      }
    }
    return path;
  }
  if (variant === "linear") {
    return points
      .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`)
      .join(" ");
  }

  let path = `M ${first.x} ${first.y}`;
  for (let index = 0; index < points.length - 1; index += 1) {
    const previous = points[index - 1] ?? points[index];
    const current = points[index];
    const next = points[index + 1];
    const after = points[index + 2] ?? next;
    if (
      previous === undefined ||
      current === undefined ||
      next === undefined ||
      after === undefined
    ) {
      continue;
    }
    const firstControlX = current.x + (next.x - previous.x) / 6;
    const firstControlY = current.y + (next.y - previous.y) / 6;
    const secondControlX = next.x - (after.x - current.x) / 6;
    const secondControlY = next.y - (after.y - current.y) / 6;
    path += ` C ${firstControlX} ${firstControlY}, ${secondControlX} ${secondControlY}, ${next.x} ${next.y}`;
  }
  return path;
}

function buildAreaPath(points: Point[], baseline: number, variant: ChartVariant): string {
  const line = buildLinePath(points, variant);
  const first = points[0];
  const last = points[points.length - 1];
  if (line.length === 0 || first === undefined || last === undefined || points.length < 2) {
    return "";
  }
  const body = line.replace(/^M\s+[^ ]+\s+[^ ]+/, "");
  return `M ${first.x} ${baseline} L ${first.x} ${first.y}${body} L ${last.x} ${baseline} Z`;
}

function inferYLabel(yLabel: unknown, values: number[]): string {
  if (typeof yLabel === "string" && yLabel.trim().length > 0) {
    return yLabel.trim();
  }
  const finite = values.filter((value) => Number.isFinite(value));
  return finite.length > 0 && finite.every((value) => value >= 0.2 && value <= 5) ? "NAV" : "Valor";
}

function inferXLabel(xLabel: unknown, labels: string[]): string | null {
  if (typeof xLabel === "string" && xLabel.trim().length > 0) {
    return xLabel.trim();
  }
  return labels.some((label) => DATE_PATTERN.test(label)) ? "Fecha" : null;
}

function PortfolioChart({ kind, ...props }: ChartProps & { kind: ChartKind }) {
  const { theme } = useTheme();
  const labels = normalizeLabels(props.labels);
  const series = normalizeSeries(props.series, labels);
  const [hidden, setHidden] = useState<ReadonlySet<string>>(() => new Set());
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const gradientId = useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const visibleSeries = series.filter((entry) => !hidden.has(entry.name));
  const allValues = visibleSeries.flatMap((entry) =>
    entry.values.filter((value) => Number.isFinite(value)),
  );
  const axis = buildYAxis(allValues);
  const chartHeight = readHeight(props.height);
  const plotWidth = VIEW_WIDTH - PLOT_LEFT - PLOT_RIGHT;
  const plotHeight = chartHeight - PLOT_TOP - PLOT_BOTTOM;
  const baseline = PLOT_TOP + plotHeight;
  const variant = readVariant(props.variant);
  const palette =
    (kind === "area" ? theme.areaChartPalette : theme.lineChartPalette) ??
    theme.defaultChartPalette ??
    (kind === "area" ? FALLBACK_AREA_PALETTE : FALLBACK_LINE_PALETTE);
  const colors = palette.length > 0 ? palette : DEFAULT_CHART_PALETTE;
  const xLabel = inferXLabel(props.xLabel, labels);
  const yLabel = inferYLabel(props.yLabel, allValues);
  const activeLabel = activeIndex === null ? "" : (labels[activeIndex] ?? "");

  function colorFor(index: number): string {
    return colors[index % colors.length] ?? DEFAULT_CHART_PALETTE[0]!;
  }

  function xFor(index: number): number {
    if (labels.length <= 1) {
      return PLOT_LEFT + plotWidth / 2;
    }
    return PLOT_LEFT + (index / (labels.length - 1)) * plotWidth;
  }

  function yFor(value: number): number {
    return PLOT_TOP + (1 - (value - axis.min) / (axis.max - axis.min)) * plotHeight;
  }

  function toggleSeries(name: string): void {
    setHidden((current) => {
      const next = new Set(current);
      if (next.has(name)) {
        next.delete(name);
        return next;
      }
      const remaining = series.filter((entry) => !next.has(entry.name) && entry.name !== name);
      if (remaining.length > 0) {
        next.add(name);
      }
      return next;
    });
  }

  if (labels.length === 0 || series.length === 0) {
    return <p className="portfolio-chart__empty">No data available for this chart.</p>;
  }

  const xTickIndices = new Set<number>();
  const stride = Math.max(1, Math.ceil(labels.length / 8));
  for (let index = 0; index < labels.length; index += stride) {
    xTickIndices.add(index);
  }
  xTickIndices.add(labels.length - 1);

  return (
    <figure className="portfolio-chart" data-chart-kind={kind}>
      <div className="portfolio-chart__context">
        <span className="portfolio-chart__pill" data-chart-axis="y">
          Eje Y: {yLabel}
        </span>
        <span className="portfolio-chart__pill" data-chart-axis="range">
          Rango: {formatExact(axis.rawMin)} – {formatExact(axis.rawMax)}
        </span>
        {xLabel !== null && (
          <span className="portfolio-chart__pill" data-chart-axis="x">
            Eje X: {xLabel}
          </span>
        )}
      </div>

      <div className="portfolio-chart__legend" aria-label="Series legend">
        {series.map((entry, index) => {
          const color = colorFor(index);
          const finiteValues = entry.values.filter((value) => Number.isFinite(value));
          const first = finiteValues[0];
          const last = finiteValues[finiteValues.length - 1];
          const isHidden = hidden.has(entry.name);
          return (
            <button
              key={`${entry.name}-${index}`}
              type="button"
              className={`portfolio-chart__legend-item${isHidden ? " is-hidden" : ""}`}
              aria-pressed={!isHidden}
              data-series-legend={entry.name}
              onClick={() => toggleSeries(entry.name)}
            >
              <span
                className="portfolio-chart__swatch"
                style={{ backgroundColor: color }}
                aria-hidden="true"
              />
              <span className="portfolio-chart__legend-copy">
                <span className="portfolio-chart__legend-name">{entry.name}</span>
                {first !== undefined && last !== undefined && finiteValues.length >= 2 && (
                  <span className="portfolio-chart__legend-range">
                    {formatExact(first)} → {formatExact(last)}
                  </span>
                )}
              </span>
            </button>
          );
        })}
      </div>

      <svg
        className="portfolio-chart__plot"
        viewBox={`0 0 ${VIEW_WIDTH} ${chartHeight}`}
        height={chartHeight}
        role="img"
        aria-label={`${kind === "area" ? "Area" : "Line"} chart${labels.length > 0 ? `: ${labels.join(", ")}` : ""}`}
      >
        <defs>
          {visibleSeries.map((entry) => {
            const seriesIndex = series.indexOf(entry);
            const color = colorFor(seriesIndex);
            return (
              <linearGradient
                key={`${entry.name}-${seriesIndex}`}
                id={`${gradientId}-${seriesIndex}`}
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop offset="0%" stopColor={color} stopOpacity="0.34" />
                <stop offset="100%" stopColor={color} stopOpacity="0.03" />
              </linearGradient>
            );
          })}
        </defs>

        {axis.ticks.map((tick) => {
          const y = yFor(tick);
          return (
            <g key={tick}>
              <line
                className="portfolio-chart__grid"
                x1={PLOT_LEFT}
                x2={VIEW_WIDTH - PLOT_RIGHT}
                y1={y}
                y2={y}
              />
              <text
                className="portfolio-chart__axis-label"
                data-chart-tick="y"
                x={PLOT_LEFT - 10}
                y={y + 4}
                textAnchor="end"
              >
                {formatTick(tick, axis.decimals)}
              </text>
            </g>
          );
        })}

        {[...xTickIndices]
          .sort((left, right) => left - right)
          .map((index) => (
            <text
              key={`${labels[index]}-${index}`}
              className="portfolio-chart__axis-label portfolio-chart__axis-label--x"
              data-chart-tick="x"
              x={xFor(index)}
              y={chartHeight - 12}
              textAnchor="middle"
            >
              {labels[index]}
            </text>
          ))}

        {visibleSeries.map((entry) => {
          const seriesIndex = series.indexOf(entry);
          const color = colorFor(seriesIndex);
          const points = entry.values.flatMap((value, index) =>
            Number.isFinite(value) ? [{ x: xFor(index), y: yFor(value) }] : [],
          );
          const linePath = buildLinePath(points, variant);
          return (
            <g key={`${entry.name}-${seriesIndex}`} data-chart-series={entry.name}>
              {kind === "area" && (
                <path
                  d={buildAreaPath(points, baseline, variant)}
                  fill={`url(#${gradientId}-${seriesIndex})`}
                  stroke="none"
                />
              )}
              <path
                d={linePath}
                fill="none"
                stroke={color}
                strokeWidth="2.4"
                strokeLinecap="round"
                strokeLinejoin="round"
                vectorEffect="non-scaling-stroke"
              />
              {points.map((point, pointIndex) => (
                <circle
                  key={pointIndex}
                  cx={point.x}
                  cy={point.y}
                  r="3.5"
                  fill={color}
                  stroke="var(--openui-sunk, #ffffff)"
                  strokeWidth="1.5"
                  vectorEffect="non-scaling-stroke"
                />
              ))}
            </g>
          );
        })}

        {labels.map((label, index) => {
          const width = Math.max(plotWidth / Math.max(labels.length, 1), 1);
          const x = Math.max(PLOT_LEFT, xFor(index) - width / 2);
          const values = visibleSeries
            .map((entry) => {
              const value = entry.values[index];
              return Number.isFinite(value)
                ? `${entry.name} ${formatExact(value as number)}`
                : `${entry.name} –`;
            })
            .join(", ");
          return (
            <rect
              key={`hover-${label}-${index}`}
              x={x}
              y={PLOT_TOP}
              width={width}
              height={plotHeight}
              fill="transparent"
              tabIndex={0}
              role="img"
              aria-label={`${label}: ${values}`}
              onMouseEnter={() => setActiveIndex(index)}
              onMouseLeave={() => setActiveIndex(null)}
              onFocus={() => setActiveIndex(index)}
              onBlur={() => setActiveIndex(null)}
            />
          );
        })}

        {activeIndex !== null && (
          <line
            className="portfolio-chart__crosshair"
            x1={xFor(activeIndex)}
            x2={xFor(activeIndex)}
            y1={PLOT_TOP}
            y2={baseline}
          />
        )}

        {activeIndex !== null && (
          <g
            className="portfolio-chart__tooltip"
            pointerEvents="none"
            transform={`translate(${Math.min(
              Math.max(xFor(activeIndex) - 105, PLOT_LEFT),
              VIEW_WIDTH - PLOT_RIGHT - 210,
            )}, ${PLOT_TOP + 8})`}
          >
            <rect width="210" height={28 + visibleSeries.length * 18} rx="9" />
            <text className="portfolio-chart__tooltip-title" x="12" y="19">
              {activeLabel}
            </text>
            {visibleSeries.map((entry, index) => {
              const value = entry.values[activeIndex];
              return (
                <g key={entry.name} transform={`translate(12, ${36 + index * 18})`}>
                  <circle r="4" fill={colorFor(series.indexOf(entry))} />
                  <text x="10" y="4">
                    {entry.name}: {Number.isFinite(value) ? formatExact(value as number) : "–"}
                  </text>
                </g>
              );
            })}
          </g>
        )}
      </svg>
    </figure>
  );
}

function PortfolioLineChart(props: ChartProps) {
  return <PortfolioChart kind="line" {...props} />;
}

function PortfolioAreaChart(props: ChartProps) {
  return <PortfolioChart kind="area" {...props} />;
}

function createPortfolioComponents(library: SchemaLibrary) {
  return {
    textContent: defineComponent({
      name: "TextContent",
      props: schemaOf(library, "TextContent"),
      description:
        'Text block. Supports markdown. Optional size: "small" | "default" | "large" | "small-heavy" | "large-heavy".',
      component: ({ props }) => <PortfolioTextContent text={props.text} size={props.size} />,
    }),
    inlineHeader: defineComponent({
      name: "InlineHeader",
      props: schemaOf(library, "InlineHeader"),
      description:
        "Compact section heading with an optional one-line description, for use inside cards.",
      component: ({ props }) => (
        <PortfolioInlineHeader heading={props.heading} description={props.description} />
      ),
    }),
    table: defineComponent({
      name: "Table",
      props: schemaOf(library, "Table"),
      description: "Data table — column-oriented. Each Col holds its own data array.",
      component: ({ props, renderNode }) => (
        <PortfolioTable columns={props.columns} renderNode={renderNode} />
      ),
    }),
    lineChart: defineComponent({
      name: "LineChart",
      props: schemaOf(library, "LineChart"),
      description: "Lines over categories; use for trends and continuous data over time",
      component: ({ props }) => <PortfolioLineChart {...(props as ChartProps)} />,
    }),
    areaChart: defineComponent({
      name: "AreaChart",
      props: schemaOf(library, "AreaChart"),
      description: "Filled area under lines; use for cumulative totals or volume trends over time",
      component: ({ props }) => <PortfolioAreaChart {...(props as ChartProps)} />,
    }),
  };
}

const reportComponents = createPortfolioComponents(openuiLibrary);
const chatComponents = createPortfolioComponents(openuiChatLibrary);

export const portfolioReportLibrary = openuiLibrary.extend({
  components: {
    override: [
      reportComponents.textContent,
      reportComponents.inlineHeader,
      reportComponents.table,
      reportComponents.lineChart,
      reportComponents.areaChart,
    ],
  },
});

export const portfolioChatLibrary = openuiChatLibrary.extend({
  components: {
    override: [
      chatComponents.textContent,
      chatComponents.inlineHeader,
      chatComponents.table,
      chatComponents.lineChart,
      chatComponents.areaChart,
    ],
  },
});
