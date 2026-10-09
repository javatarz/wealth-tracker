import { useState } from "react";

import type { BenchmarkDefinition } from "./benchmarkConfig";
import { BenchmarkPicker } from "./BenchmarkPicker";
import {
  saveInstrumentBenchmark,
  type InstrumentBenchmark,
} from "./instrumentBenchmarks";
import { classLabel, nameOf } from "./benchmarkOptions";

/** The sentinel the per-Instrument picker uses to clear its override. */
const CLEAR = "";

export function InstrumentOverride({
  instrument,
  available,
}: {
  instrument: InstrumentBenchmark;
  available: BenchmarkDefinition[];
}) {
  const [saved, setSaved] = useState(instrument);

  async function change(selected: string) {
    const result = await saveInstrumentBenchmark(
      instrument.instrument_id,
      selected === CLEAR ? null : selected,
    );
    if (result.kind === "ok") {
      setSaved(result.instrument);
    }
  }

  const label = `Use ${classLabel(saved.asset_class)} — ${nameOf(
    available,
    saved.resolved_key,
  )}`;

  return (
    <li className="instrument">
      <span className="instrument-name">{saved.name}</span>
      <label className="picker">
        Benchmark
        <BenchmarkPicker
          value={saved.override_key ?? CLEAR}
          available={available}
          emptyLabel={label}
          onChange={(next) => {
            void change(next);
          }}
        />
      </label>
    </li>
  );
}
