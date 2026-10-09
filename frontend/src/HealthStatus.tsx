import { useEffect, useState } from "react";

import { api } from "./api/client";

type Health =
  | { kind: "loading" }
  | { kind: "ok"; status: string }
  | { kind: "error"; message: string };

export function HealthStatus() {
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
    <p className="muted small">
      API health: {health.kind === "loading" && <span>checking…</span>}
      {health.kind === "ok" && <span>{health.status}</span>}
      {health.kind === "error" && <span role="alert">{health.message}</span>}
    </p>
  );
}
