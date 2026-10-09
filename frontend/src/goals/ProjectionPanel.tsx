import { useEffect, useState } from "react";

import {
  loadProjection,
  type ProjectionResult,
  type ProjectionView,
} from "./goalProjection";
import { formatDecimal } from "../statements/formatDecimal";
import { ProjectionChart } from "./ProjectionChart";

type ProjectionState = { kind: "loading" } | ProjectionResult;

const STATUS_LABELS: Record<string, string> = {
  exceeded: "Exceeded",
  on_track: "On track",
  at_risk: "At risk",
  off_track: "At risk",
  insufficient_data: "Insufficient data",
};

const STATUS_TONES: Record<string, string> = {
  exceeded: "good",
  on_track: "good",
  at_risk: "warn",
  off_track: "bad",
  insufficient_data: "muted",
};

export function ProjectionPanel({ goalId }: { goalId: string }) {
  const [state, setState] = useState<ProjectionState>({ kind: "loading" });

  useEffect(() => {
    void loadProjection(goalId).then(setState);
  }, [goalId]);

  return state.kind === "ok" ? (
    <ProjectionBody projection={state.projection} />
  ) : null;
}

function ProjectionBody({ projection }: { projection: ProjectionView }) {
  return (
    <section className="projection">
      <StatusBadge status={projection.status} />
      <ProjectionChart projection={projection} />
      <p className="goal-figures">
        Projected <strong>₹{formatDecimal(projection.projected_value)}</strong>{" "}
        by {projection.target_date} · target ₹
        {formatDecimal(projection.target_amount)}
      </p>
    </section>
  );
}

function StatusBadge({ status }: { status: string }) {
  return <span className={`badge ${toneOf(status)}`}>{labelOf(status)}</span>;
}

function labelOf(status: string): string {
  return STATUS_LABELS[status] ?? status;
}

function toneOf(status: string): string {
  return STATUS_TONES[status] ?? "muted";
}
