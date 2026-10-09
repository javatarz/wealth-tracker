import type { BenchmarkPoint } from "./benchmarkReturns";

export interface OverlayLine {
  key: string;
  name: string;
  points: BenchmarkPoint[];
}

export interface OverlayGeometry {
  key: string;
  path: string;
}

interface Interval {
  low: number;
  high: number;
}

interface Domain extends Interval {
  first: number;
  last: number;
}

export const WIDTH = 720;
export const HEIGHT = 240;
export const VIEW_BOX = "0 0 720 240";

const PADDING = 24;
const X_AXIS: Interval = { low: PADDING, high: WIDTH - PADDING };
const Y_AXIS: Interval = { low: HEIGHT - PADDING, high: PADDING };

/** Maps every line onto one shared set of SVG coordinates (ADR 0017). */
export function overlayGeometry(lines: OverlayLine[]): OverlayGeometry[] {
  const points = lines.flatMap((line) => line.points);
  if (points.length === 0) {
    return [];
  }
  const domain = domainOf(points);
  return lines.map((line) => ({
    key: line.key,
    path: pathOf(line.points, domain),
  }));
}

function domainOf(points: BenchmarkPoint[]): Domain {
  const dates = points.map((point) => Date.parse(point.date));
  const values = points.map((point) => Number(point.value));
  return {
    first: Math.min(...dates),
    last: Math.max(...dates),
    low: Math.min(...values),
    high: Math.max(...values),
  };
}

function pathOf(points: BenchmarkPoint[], domain: Domain): string {
  return points.map((point) => command(point, domain)).join(" ");
}

function command(point: BenchmarkPoint, domain: Domain): string {
  const x = scale(
    Date.parse(point.date),
    { low: domain.first, high: domain.last },
    X_AXIS,
  );
  const y = scale(
    Number(point.value),
    { low: domain.low, high: domain.high },
    Y_AXIS,
  );
  return `L ${plain(x)} ${plain(y)}`;
}

function scale(value: number, source: Interval, target: Interval): number {
  return source.low === source.high
    ? target.low
    : target.low +
        ((value - source.low) / (source.high - source.low)) *
          (target.high - target.low);
}

function plain(value: number): string {
  return String(Math.round(value * 100) / 100);
}
