import { useEffect, useState } from "react";

import type { BenchmarkDefinition } from "./benchmarkConfig";
import {
  loadInstrumentBenchmarks,
  type InstrumentBenchmark,
} from "./instrumentBenchmarks";
import { InstrumentOverride } from "./InstrumentOverride";

export function InstrumentBenchmarks({
  available,
}: {
  available: BenchmarkDefinition[];
}) {
  const [instruments, setInstruments] = useState<InstrumentBenchmark[]>([]);

  useEffect(() => {
    void loadInstrumentBenchmarks().then((result) => {
      if (result.kind === "ok") {
        setInstruments(result.instruments);
      }
    });
  }, []);

  if (instruments.length === 0) {
    return null;
  }
  return (
    <section className="instruments" aria-labelledby="instruments-heading">
      <h3 id="instruments-heading">Per-Instrument overrides</h3>
      <ul>
        {instruments.map((instrument) => (
          <InstrumentOverride
            key={instrument.instrument_id}
            instrument={instrument}
            available={available}
          />
        ))}
      </ul>
    </section>
  );
}
