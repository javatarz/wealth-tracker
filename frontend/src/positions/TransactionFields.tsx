import { transactionTypeLabel } from "./transactionTypes";
import type { Draft } from "./addTransaction";

interface FieldSpec {
  label: string;
  name: keyof Draft;
  value: string;
  type?: string;
  options?: string[];
}

function specs(draft: Draft, allowedTypes: string[]): FieldSpec[] {
  return [
    { label: "Type", name: "type", value: draft.type, options: allowedTypes },
    { label: "Date", name: "date", value: draft.date, type: "date" },
    { label: "Units", name: "units", value: draft.units },
    { label: "Cost (₹)", name: "amount", value: draft.amount },
    { label: "Notes", name: "notes", value: draft.notes },
  ];
}

export function TransactionFields({
  draft,
  allowedTypes,
  onChange,
}: {
  draft: Draft;
  allowedTypes: string[];
  onChange: (draft: Draft) => void;
}) {
  const update = (name: keyof Draft, value: string) => {
    onChange({ ...draft, [name]: value });
  };

  return (
    <>
      {specs(draft, allowedTypes).map((spec) => (
        <Field key={spec.name} spec={spec} onValue={update} />
      ))}
    </>
  );
}

function Field({
  spec,
  onValue,
}: {
  spec: FieldSpec;
  onValue: (name: keyof Draft, value: string) => void;
}) {
  return (
    <label className="field">
      <span>{spec.label}</span>
      <Control spec={spec} onValue={onValue} />
    </label>
  );
}

function Control({
  spec,
  onValue,
}: {
  spec: FieldSpec;
  onValue: (name: keyof Draft, value: string) => void;
}) {
  const change = (value: string) => {
    onValue(spec.name, value);
  };
  if (spec.options !== undefined) {
    return (
      <select
        name={spec.name}
        value={spec.value}
        onChange={(event) => {
          change(event.target.value);
        }}
      >
        {spec.options.map((option) => (
          <option key={option} value={option}>
            {transactionTypeLabel(option)}
          </option>
        ))}
      </select>
    );
  }
  return (
    <input
      name={spec.name}
      type={spec.type}
      value={spec.value}
      onChange={(event) => {
        change(event.target.value);
      }}
    />
  );
}
