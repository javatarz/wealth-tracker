import { useEffect, useState } from "react";
import type { components } from "../api/schema.d.ts";

type HealthResponse = components["schemas"]["HealthResponse"];

type LoadState =
  | { phase: "loading" }
  | { phase: "success"; health: HealthResponse }
  | { phase: "error"; message: string };

export default function HealthPage() {
  const [state, setState] = useState<LoadState>({ phase: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function loadHealth(): Promise<void> {
      try {
        const response = await fetch("/health");
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const health = (await response.json()) as HealthResponse;
        if (!cancelled) {
          setState({ phase: "success", health });
        }
      } catch (error) {
        if (!cancelled) {
          setState({
            phase: "error",
            message: error instanceof Error ? error.message : "Unknown error",
          });
        }
      }
    }

    void loadHealth();

    return () => {
      cancelled = true;
    };
  }, []);

  if (state.phase === "loading") {
    return <p>Loading health…</p>;
  }

  if (state.phase === "error") {
    return <p role="alert">Health check failed: {state.message}</p>;
  }

  return (
    <div>
      <h1>Wealth Tracker</h1>
      <dl>
        <dt>Status</dt>
        <dd>{state.health.status}</dd>
        <dt>Version</dt>
        <dd>{state.health.version}</dd>
      </dl>
    </div>
  );
}
