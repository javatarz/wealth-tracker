import { useEffect, useState } from "react";

import { api } from "./api/client";
import { StatementImport } from "./statements/StatementImport";

type Health =
  | { kind: "loading" }
  | { kind: "ok"; status: string }
  | { kind: "error"; message: string };

export default function App() {
  const [health, setHealth] = useState<Health>({ kind: "loading" });

  useEffect(() => {
    api
      .GET("/api/health")
      .then(({ data }) => {
        setHealth(
          data
            ? { kind: "ok", status: data.status }
            : { kind: "error", message: "Unexpected response" },
        );
      })
      .catch((error: unknown) => {
        setHealth({ kind: "error", message: String(error) });
      });
  }, []);

  return (
    <main>
      <h1>Wealth Tracker</h1>
      <p className="muted small">
        API health: {health.kind === "loading" && <span>checking…</span>}
        {health.kind === "ok" && <span>{health.status}</span>}
        {health.kind === "error" && <span role="alert">{health.message}</span>}
      </p>
      <StatementImport />
    </main>
  );
}
