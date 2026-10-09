import { useState, type SubmitEvent } from "react";

import { createGoal, updateGoal } from "./goalCommands";
import { draftOf, toWrite, type GoalDraft } from "./goalDraft";
import { GoalFields } from "./GoalFields";
import type { AccountSummary, GoalSummary } from "./listGoals";

interface GoalFormProps {
  goal?: GoalSummary | undefined;
  accounts: AccountSummary[];
  onSaved: () => void;
  onCancel: () => void;
}

export function GoalForm({ goal, accounts, onSaved, onCancel }: GoalFormProps) {
  const [draft, setDraft] = useState<GoalDraft>(() => draftOf(goal));
  const [error, setError] = useState<string | null>(null);

  async function save(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    const result = await send(goal, toWrite(draft));
    if (result.kind === "error") {
      setError(result.message);
      return;
    }
    onSaved();
  }

  return (
    <form className="callout goal-form" onSubmit={(event) => void save(event)}>
      <GoalFields draft={draft} accounts={accounts} onChange={setDraft} />
      <div className="goal-form-actions">
        <button type="submit" className="btn btn-primary">
          {goal ? "Save changes" : "Create Goal"}
        </button>
        <button type="button" className="btn" onClick={onCancel}>
          Cancel
        </button>
      </div>
      {error !== null && (
        <p role="alert" className="callout bad">
          {error}
        </p>
      )}
    </form>
  );
}

function send(goal: GoalSummary | undefined, body: ReturnType<typeof toWrite>) {
  return goal ? updateGoal(goal.id, body) : createGoal(body);
}
