import { useState } from "react";

import {
  draftError,
  EMPTY_DRAFT,
  type AddTransactionState,
  type Draft,
} from "./addTransaction";
import { addTransaction, type PositionDetail } from "./positionDetail";

export interface ManualEntry {
  draft: Draft;
  state: AddTransactionState;
  entryType: string;
  edit: (draft: Draft) => void;
  submit: () => Promise<void>;
}

export function useManualEntry(
  position: PositionDetail,
  today: string,
  onAdded: (position: PositionDetail) => void,
): ManualEntry {
  const [draft, setDraft] = useState<Draft>(EMPTY_DRAFT);
  const [state, setState] = useState<AddTransactionState>({ kind: "idle" });
  const entryType = draft.type || (position.allowed_types[0] ?? "");

  async function submit() {
    const submitted = { ...draft, type: entryType };
    const message = draftError(submitted, today);
    if (message !== null) {
      setState({ kind: "invalid", message });
      return;
    }
    await save(submitted);
  }

  async function save(submitted: Draft) {
    setState({ kind: "saving" });
    const result = await addTransaction(position.id, requestFrom(submitted));
    setDraft(EMPTY_DRAFT);
    if (result.kind === "error") {
      setState({ kind: "invalid", message: result.message });
      return;
    }
    setState({ kind: "idle" });
    onAdded(result.position);
  }

  return { draft, state, entryType, edit: setDraft, submit };
}

function requestFrom(draft: Draft) {
  return {
    type: draft.type,
    date: draft.date,
    units: draft.units,
    amount: draft.amount === "" ? null : draft.amount,
    notes: draft.notes,
  };
}
