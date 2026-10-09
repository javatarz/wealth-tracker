import { formatDecimal } from "../statements/formatDecimal";
import type { ProjectionView } from "./goalProjection";

interface ProjectionChartProps {
  projection: ProjectionView;
}

const WIDTH = 320;
const HEIGHT = 160;
const PAD = 8;
const PLOT_W = WIDTH - PAD * 2;
const PLOT_H = HEIGHT - PAD * 2;

interface Series {
  target: number;
  max: number;
}

export function ProjectionChart({ projection }: ProjectionChartProps) {
  const series = seriesOf(projection);
  const values = projection.trajectory.map((point) => Number(point.value));
  const path = polyline(values, series);
  const targetY = y(series.target, series);
  const label = `Projected ${formatDecimal(projection.projected_value)} against a target of ${formatDecimal(projection.target_amount)}`;
  return (
    <svg
      className="projection-chart"
      viewBox={`0 0 ${String(WIDTH)} ${String(HEIGHT)}`}
      role="img"
      aria-label={label}
    >
      <line
        className="projection-target"
        x1={PAD}
        y1={targetY}
        x2={PAD + PLOT_W}
        y2={targetY}
      />
      <polyline className="projection-line" points={path} />
    </svg>
  );
}

function seriesOf(projection: ProjectionView): Series {
  const values = projection.trajectory.map((point) => Number(point.value));
  const target = Number(projection.target_amount);
  const max = Math.max(target, ...values);
  return { target, max: max || 1 };
}

function polyline(values: number[], series: Series): string {
  const lastIndex = Math.max(values.length - 1, 1);
  return values
    .map((value, index) => {
      const px = PAD + (PLOT_W * index) / lastIndex;
      return `${px.toFixed(1)},${y(value, series).toFixed(1)}`;
    })
    .join(" ");
}

function y(value: number, series: Series): number {
  const fraction = Math.min(Math.max(value / series.max, 0), 1);
  return PAD + PLOT_H * (1 - fraction);
}
