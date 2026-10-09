import { useEffect, useState } from "react";

import { loadBenchmarkConfig, type BenchmarkConfig } from "./benchmarkConfig";

export type ConfigState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; config: BenchmarkConfig };

export function useBenchmarkConfig(): ConfigState {
  const [state, setState] = useState<ConfigState>({ kind: "loading" });

  useEffect(() => {
    void loadBenchmarkConfig().then((result) => {
      setState(
        result.kind === "ok"
          ? { kind: "ready", config: result.config }
          : { kind: "error", message: result.message },
      );
    });
  }, []);

  return state;
}
