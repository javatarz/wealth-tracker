import { formatDecimal } from "../statements/formatDecimal";
import { deleteGoal } from "./goalCommands";
import type { GoalSummary } from "./listGoals";

interface GoalCardsProps {
  goals: GoalSummary[];
  onEdit: (goal: GoalSummary) => void;
  onDelete: () => void;
}

export function GoalCards({ goals, onEdit, onDelete }: GoalCardsProps) {
  if (goals.length === 0) {
    return <p className="muted">No Goals yet. Set one to start tracking it.</p>;
  }
  return (
    <div className="goal-list">
      {goals.map((goal) => (
        <GoalCard
          key={goal.id}
          goal={goal}
          onEdit={() => {
            onEdit(goal);
          }}
          onDelete={() => {
            void deleteGoal(goal.id).then(() => {
              onDelete();
            });
          }}
        />
      ))}
    </div>
  );
}

function GoalCard({
  goal,
  onEdit,
  onDelete,
}: {
  goal: GoalSummary;
  onEdit: () => void;
  onDelete: () => void;
}) {
  return (
    <article className="goal-card">
      <header className="goal-card-head">
        <h3>{goal.name}</h3>
        <span className="muted small">by {goal.target_date}</span>
      </header>
      <progress
        className="goal-progress"
        max={100}
        value={percent(goal.percent_funded)}
      />
      <p className="goal-figures">
        <strong>₹{formatDecimal(goal.current_value)}</strong> of ₹
        {formatDecimal(goal.target_amount)} ·{" "}
        {formatDecimal(goal.percent_funded)}%
      </p>
      <div className="goal-card-actions">
        <button type="button" className="btn" onClick={onEdit}>
          Edit
        </button>
        <button type="button" className="btn" onClick={onDelete}>
          Delete
        </button>
      </div>
    </article>
  );
}

function percent(funded: string): string {
  return String(Math.min(100, Math.max(0, Number(funded))));
}
