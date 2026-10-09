import { type ReactNode } from "react";

import { GoalBoard } from "./GoalBoard";
import { useGoals, type GoalsState } from "./useGoals";

type Kind = GoalsState["kind"];
type StateOf<K extends Kind> = Extract<GoalsState, { kind: K }>;
type View<K extends Kind> = (
  state: StateOf<K>,
  reload: () => void,
) => ReactNode;

const views: { [K in Kind]: View<K> } = {
  loading: () => (
    <p role="status" className="muted">
      Loading Goals…
    </p>
  ),
  error: ({ message }) => (
    <p role="alert" className="callout bad">
      {message}
    </p>
  ),
  ok: ({ goals, accounts }: Extract<GoalsState, { kind: "ok" }>, reload) => (
    <GoalBoard goals={goals} accounts={accounts} reload={reload} />
  ),
};

function renderView<K extends Kind>(
  kind: K,
  state: StateOf<K>,
  reload: () => void,
): ReactNode {
  return views[kind](state, reload);
}

export function GoalsList() {
  const { state, reload } = useGoals();

  return (
    <section aria-labelledby="goals-heading">
      <h2 id="goals-heading">Goals</h2>
      {renderView(state.kind, state, reload)}
    </section>
  );
}
