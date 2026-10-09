import { useState } from "react";

import { GoalForm } from "./GoalForm";
import { GoalCards } from "./GoalCards";
import type { AccountSummary, GoalSummary } from "./listGoals";

interface GoalBoardProps {
  goals: GoalSummary[];
  accounts: AccountSummary[];
  reload: () => void;
}

export function GoalBoard({ goals, accounts, reload }: GoalBoardProps) {
  const [editing, setEditing] = useState<GoalSummary | null | undefined>(
    undefined,
  );
  const close = () => {
    setEditing(undefined);
    reload();
  };

  return (
    <>
      <button
        type="button"
        className="btn btn-primary"
        onClick={() => {
          setEditing(null);
        }}
      >
        New Goal
      </button>
      {editing !== undefined && (
        <GoalForm
          goal={editing ?? undefined}
          accounts={accounts}
          onSaved={close}
          onCancel={close}
        />
      )}
      <GoalCards goals={goals} onEdit={setEditing} onDelete={reload} />
    </>
  );
}
