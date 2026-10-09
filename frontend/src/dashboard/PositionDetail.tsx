import type { DashboardPosition } from "./dashboardApi";

export interface PositionDetailProps {
  position: DashboardPosition;
  onBack: () => void;
}

export function PositionDetail({ position, onBack }: PositionDetailProps) {
  return (
    <section aria-labelledby="position-heading">
      <button type="button" className="btn" onClick={onBack}>
        ← Back to dashboard
      </button>
      <h2 id="position-heading">{position.scheme}</h2>
      <p className="muted">{position.account}</p>
      <p className="muted">
        Transaction list, lot breakdown and reconciliation timeline arrive with
        the Position detail screen.
      </p>
    </section>
  );
}
