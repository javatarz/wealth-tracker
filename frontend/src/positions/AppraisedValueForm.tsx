import { useState } from "react";

import type { Appraisal, AppraisalResult } from "./valuation";

const TODAY = new Date().toISOString().slice(0, 10);

interface AppraisedValueFormProps {
  onSave: (appraisal: Appraisal) => Promise<AppraisalResult>;
}

type OnChange = (appraisal: Appraisal) => void;

export function AppraisedValueForm({ onSave }: AppraisedValueFormProps) {
  const [state, setState] = useState<Appraisal>({ date: TODAY, value: "" });
  const [message, setMessage] = useState<string | null>(null);
  const save = async () => {
    setMessage(messageFor(await onSave(state)));
    setState({ date: state.date, value: "" });
  };
  return (
    <form
      className="callout"
      aria-labelledby="appraisal-heading"
      onSubmit={(event) => {
        event.preventDefault();
        void save();
      }}
    >
      <h3 id="appraisal-heading">Set an appraised value</h3>
      <AppraisalFields appraisal={state} onChange={setState} />
      <button
        type="submit"
        className="btn btn-primary"
        disabled={state.value === ""}
      >
        Record appraisal
      </button>
      {message !== null && <p role="status">{message}</p>}
    </form>
  );
}

function AppraisalFields({
  appraisal,
  onChange,
}: {
  appraisal: Appraisal;
  onChange: OnChange;
}) {
  return (
    <>
      <label>
        As of
        <input
          type="date"
          value={appraisal.date}
          onChange={(event) => {
            onChange({ ...appraisal, date: event.target.value });
          }}
        />
      </label>
      <label>
        Value (₹)
        <input
          type="text"
          inputMode="decimal"
          autoComplete="off"
          value={appraisal.value}
          onChange={(event) => {
            onChange({ ...appraisal, value: event.target.value });
          }}
        />
      </label>
    </>
  );
}

function messageFor(result: AppraisalResult): string {
  return result.kind === "error" ? result.message : "Appraised value recorded.";
}
