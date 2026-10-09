import { useState } from "react";

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
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}

interface GoalCardProps {
  goal: GoalSummary;
  onEdit: (goal: GoalSummary) => void;
  onDelete: () => void;
}

function GoalCard({ goal, onEdit, onDelete }: GoalCardProps) {
  const [confirming, setConfirming] = useState(false);

  const remove = async () => {
    await deleteGoal(goal.id);
    onDelete();
  };

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
      <GoalCardActions
        confirming={confirming}
        onEdit={() => {
          onEdit(goal);
        }}
        onAsk={() => {
          setConfirming(true);
        }}
        onCancel={() => {
          setConfirming(false);
        }}
        onConfirm={() => void remove()}
      />
    </article>
  );
}

interface ActionsProps {
  confirming: boolean;
  onEdit: () => void;
  onAsk: () => void;
  onCancel: () => void;
  onConfirm: () => void;
}

function GoalCardActions({
  confirming,
  onEdit,
  onAsk,
  onCancel,
  onConfirm,
}: ActionsProps) {
  return (
    <div className="goal-card-actions">
      <button type="button" className="btn" onClick={onEdit}>
        Edit
      </button>
      {confirming ? (
        <>
          <span className="muted small">Delete this Goal?</span>
          <button type="button" className="btn bad-text" onClick={onConfirm}>
            Confirm delete
          </button>
          <button type="button" className="btn" onClick={onCancel}>
            Keep
          </button>
        </>
      ) : (
        <button type="button" className="btn" onClick={onAsk}>
          Delete
        </button>
      )}
    </div>
  );
}

function percent(funded: string): string {
  return String(Math.min(100, Math.max(0, Number(funded))));
}
