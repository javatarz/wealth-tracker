import type { IncomeDraft } from "./incomeDraft";
import {
  dispositionLabel,
  dispositionsFor,
  incomeTypeLabel,
} from "./incomeTypes";

interface FieldSpec {
  label: string;
  name: keyof IncomeDraft;
  value: string;
  type?: string;
  options?: string[];
  optionLabel?: (option: string) => string;
}

function specs(
  draft: IncomeDraft,
  allowedTypes: string[],
  reinvestable: boolean,
): FieldSpec[] {
  const type: FieldSpec = {
    label: "Income type",
    name: "type",
    value: draft.type,
    options: allowedTypes,
    optionLabel: incomeTypeLabel,
  };
  const date: FieldSpec = {
    label: "Income date",
    name: "date",
    value: draft.date,
    type: "date",
  };
  const amount: FieldSpec = {
    label: "Gross amount (₹)",
    name: "amount",
    value: draft.amount,
  };
  const tax: FieldSpec = {
    label: "Tax deducted (₹, optional)",
    name: "tax",
    value: draft.tax,
  };
  const disposition: FieldSpec = {
    label: "Disposition",
    name: "disposition",
    value: draft.disposition,
    options: dispositionsFor(reinvestable),
    optionLabel: dispositionLabel,
  };
  return [type, date, amount, tax, disposition, ...unitsField(draft)];
}

function unitsField(draft: IncomeDraft): FieldSpec[] {
  if (draft.disposition !== "reinvested") {
    return [];
  }
  return [{ label: "Reinvestment NAV (₹)", name: "nav", value: draft.nav }];
}

export function IncomeFields({
  draft,
  allowedTypes,
  reinvestable,
  onChange,
}: {
  draft: IncomeDraft;
  allowedTypes: string[];
  reinvestable: boolean;
  onChange: (draft: IncomeDraft) => void;
}) {
  const update = (name: keyof IncomeDraft, value: string) => {
    onChange({ ...draft, [name]: value });
  };

  return (
    <>
      {specs(draft, allowedTypes, reinvestable).map((spec) => (
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
  onValue: (name: keyof IncomeDraft, value: string) => void;
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
  onValue: (name: keyof IncomeDraft, value: string) => void;
}) {
  const change = (value: string) => {
    onValue(spec.name, value);
  };
  if (spec.options !== undefined) {
    return (
      <select
        name={spec.name}
        aria-label={spec.label}
        value={spec.value}
        onChange={(event) => {
          change(event.target.value);
        }}
      >
        {spec.options.map((option) => (
          <option key={option} value={option}>
            {(spec.optionLabel ?? identity)(option)}
          </option>
        ))}
      </select>
    );
  }
  return (
    <input
      name={spec.name}
      aria-label={spec.label}
      type={spec.type}
      value={spec.value}
      onChange={(event) => {
        change(event.target.value);
      }}
    />
  );
}

function identity(option: string): string {
  return option;
}
