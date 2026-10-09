import { useState } from "react";

import {
  EMPTY_INCOME_DRAFT,
  incomeDraftError,
  type IncomeDraft,
  type IncomeFormState,
} from "./incomeDraft";
import {
  addIncome,
  type IncomeRequest,
  type PositionDetail,
} from "./positionDetail";

export interface IncomeEntryForm {
  draft: IncomeDraft;
  state: IncomeFormState;
  incomeType: string;
  edit: (draft: IncomeDraft) => void;
  submit: () => Promise<void>;
}

export function useIncome(
  position: PositionDetail,
  today: string,
  onRecorded: (position: PositionDetail) => void,
): IncomeEntryForm {
  const defaultDraft: IncomeDraft = {
    ...EMPTY_INCOME_DRAFT,
    disposition: position.reinvestable ? "reinvested" : "withdrawn",
  };
  const [draft, setDraft] = useState<IncomeDraft>(defaultDraft);
  const [state, setState] = useState<IncomeFormState>({ kind: "idle" });
  const incomeType = draft.type || (position.allowed_income_types[0] ?? "");

  async function submit() {
    const submitted = { ...draft, type: incomeType };
    const message = incomeDraftError(submitted, today);
    if (message !== null) {
      setState({ kind: "invalid", message });
      return;
    }
    await save(submitted);
  }

  async function save(submitted: IncomeDraft) {
    setState({ kind: "saving" });
    const result = await addIncome(position.id, requestFrom(submitted));
    setDraft(defaultDraft);
    if (result.kind === "error") {
      setState({ kind: "invalid", message: result.message });
      return;
    }
    setState({ kind: "idle" });
    onRecorded(result.position);
  }

  return { draft, state, incomeType, edit: setDraft, submit };
}

function requestFrom(draft: IncomeDraft): IncomeRequest {
  const reinvested = draft.disposition === "reinvested";
  return {
    type: draft.type,
    date: draft.date,
    amount: draft.amount,
    tax: draft.tax === "" ? null : draft.tax,
    reinvested,
    nav: reinvested && draft.nav !== "" ? draft.nav : null,
  };
}
