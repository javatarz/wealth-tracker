import { api } from "../api/client";
import type { components } from "../api/schema";

export type InstrumentBenchmark =
  components["schemas"]["InstrumentBenchmarkOut"];

export type InstrumentsResult =
  | { kind: "ok"; instruments: InstrumentBenchmark[] }
  | { kind: "error"; message: string };

export type SaveResult =
  | { kind: "ok"; instrument: InstrumentBenchmark }
  | { kind: "error"; message: string };

const UNREACHABLE = "Couldn't reach the Wealth Tracker server.";
const LOAD_FAILED = "Couldn't load your Instruments.";
const SAVE_REJECTED = "The Instrument override was rejected.";

export async function loadInstrumentBenchmarks(): Promise<InstrumentsResult> {
  try {
    const { data } = await api.GET("/api/benchmarks/instruments");
    return data
      ? { kind: "ok", instruments: data }
      : { kind: "error", message: LOAD_FAILED };
  } catch {
    return { kind: "error", message: UNREACHABLE };
  }
}

export async function saveInstrumentBenchmark(
  instrumentId: string,
  benchmark: string | null,
): Promise<SaveResult> {
  try {
    const { data } = await api.PUT(
      "/api/benchmarks/instruments/{instrument_id}",
      {
        params: { path: { instrument_id: instrumentId } },
        body: { benchmark },
      },
    );
    return data
      ? { kind: "ok", instrument: data }
      : { kind: "error", message: SAVE_REJECTED };
  } catch {
    return { kind: "error", message: UNREACHABLE };
  }
}
