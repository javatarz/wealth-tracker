import { useState } from "react";

import {
  saveAssetClassBenchmark,
  type BenchmarkDefinition,
} from "./benchmarkConfig";
import { BenchmarkPicker } from "./BenchmarkPicker";
import { classLabel, nameOf } from "./benchmarkOptions";

export function AssetClassSection({
  assetClass,
  assignedKey,
  overridden,
  available,
  onSaved,
}: {
  assetClass: string;
  assignedKey: string;
  overridden: boolean;
  available: BenchmarkDefinition[];
  onSaved: (assetClass: string, key: string) => void;
}) {
  const [key, setKey] = useState(assignedKey);
  async function change(benchmark: string) {
    const result = await saveAssetClassBenchmark(assetClass, benchmark);
    if (result.kind === "ok") {
      setKey(result.assetClass.assigned_key);
      onSaved(assetClass, result.assetClass.assigned_key);
    }
  }
  return (
    <details className="asset-class" open={overridden}>
      <summary>
        {classLabel(assetClass)} — {nameOf(available, key)}
        {overridden && <span className="badge">overridden</span>}
      </summary>
      <label className="picker">
        Benchmark
        <BenchmarkPicker
          value={key}
          available={available}
          onChange={(next) => {
            void change(next);
          }}
        />
      </label>
    </details>
  );
}
