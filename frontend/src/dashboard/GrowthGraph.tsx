import type { NetWorthPoint } from "./dashboardApi";

const WIDTH = 640;
const HEIGHT = 220;
const PAD_X = 40;
const PAD_Y = 24;
const VIEW_BOX = `0 0 ${String(WIDTH)} ${String(HEIGHT)}`;

interface Plotted {
  x: number;
  y: number;
}

export function GrowthGraph({ series }: { series: NetWorthPoint[] }) {
  if (series.length < 2) {
    return (
      <p className="muted">
        Not enough history yet to draw the Net Worth graph.
      </p>
    );
  }

  const points = plot(series);
  const line = points
    .map((point) => `${point.x.toFixed(1)},${point.y.toFixed(1)}`)
    .join(" ");

  return (
    <figure className="growth-graph">
      <svg
        role="img"
        aria-label="Net Worth over time"
        viewBox={VIEW_BOX}
        preserveAspectRatio="none"
      >
        <polyline
          points={line}
          fill="none"
          stroke="var(--ink)"
          strokeWidth="2"
        />
      </svg>
      <figcaption className="muted small">
        {series.length} points · {series[0]?.date} to{" "}
        {series[series.length - 1]?.date}
      </figcaption>
    </figure>
  );
}

function plot(series: NetWorthPoint[]): Plotted[] {
  const values = series.map((point) => Number(point.value));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const usableWidth = WIDTH - PAD_X * 2;
  const usableHeight = HEIGHT - PAD_Y * 2;
  const step = usableWidth / (series.length - 1);
  return values.map((value, index) => ({
    x: PAD_X + index * step,
    y: HEIGHT - PAD_Y - ((value - min) / span) * usableHeight,
  }));
}
