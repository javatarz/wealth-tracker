import { useState } from "react";

import { BenchmarkOverlay } from "./BenchmarkOverlay";
import { BenchmarkPicker } from "./BenchmarkPicker";
import type { BenchmarkDefinition } from "./benchmarkConfig";
import { nameOf } from "./benchmarkOptions";

const ONE_YEAR = 365;

function iso(today: string): { from: string; to: string } {
  const start = new Date(today);
  start.setDate(start.getDate() - ONE_YEAR);
  return { from: start.toISOString().slice(0, 10), to: today };
}

/** A preview of a Benchmark's growth line, the same overlay the dashboard draws. */
export function BenchmarkPreview({
  available,
}: {
  available: BenchmarkDefinition[];
}) {
  const [key, setKey] = useState(available[0]?.key ?? "");
  const { from, to } = iso(new Date().toISOString().slice(0, 10));

  if (available.length === 0) {
    return null;
  }
  return (
    <section aria-labelledby="preview-heading" className="preview">
      <h3 id="preview-heading">Benchmark growth</h3>
      <label className="picker">
        Benchmark
        <BenchmarkPicker value={key} available={available} onChange={setKey} />
      </label>
      <BenchmarkOverlay
        benchmark={key}
        name={nameOf(available, key)}
        from={from}
        to={to}
      />
    </section>
  );
}
