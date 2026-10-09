import type { ChangeEvent } from "react";

import { toggle, type GoalDraft } from "./goalDraft";
import type { AccountSummary } from "./listGoals";

interface GoalFieldsProps {
  draft: GoalDraft;
  accounts: AccountSummary[];
  onChange: (draft: GoalDraft) => void;
}

const STRATEGIES = [
  { value: "", label: "None" },
  { value: "cagr", label: "Fixed CAGR" },
  { value: "trailing_window", label: "Trailing window average" },
] as const;

const RATE_FIELDS: Record<
  string,
  { label: string; key: "cagrRate" | "trailingWindowYears" } | undefined
> = {
  cagr: { label: "CAGR rate (e.g. 0.12)", key: "cagrRate" },
  trailing_window: {
    label: "Window (years)",
    key: "trailingWindowYears",
  },
};

export function GoalFields({ draft, accounts, onChange }: GoalFieldsProps) {
  const edit = (patch: Partial<GoalDraft>) => {
    onChange({ ...draft, ...patch });
  };

  return (
    <>
      <TextField
        label="Goal name"
        value={draft.name}
        onChange={(name) => {
          edit({ name });
        }}
      />
      <TextField
        label="Target amount (₹)"
        inputMode="decimal"
        value={draft.targetAmount}
        onChange={(targetAmount) => {
          edit({ targetAmount });
        }}
      />
      <TextField
        label="Target date"
        type="date"
        value={draft.targetDate}
        onChange={(targetDate) => {
          edit({ targetDate });
        }}
      />
      <StrategyPicker draft={draft} onChange={edit} />
      <AccountPicker accounts={accounts} draft={draft} onChange={onChange} />
    </>
  );
}

function StrategyPicker({
  draft,
  onChange,
}: {
  draft: GoalDraft;
  onChange: (patch: Partial<GoalDraft>) => void;
}) {
  const field = RATE_FIELDS[draft.projectionStrategy];
  return (
    <label>
      Projection strategy
      <select
        value={draft.projectionStrategy}
        onChange={(event) => {
          onChange({ projectionStrategy: event.target.value });
        }}
      >
        {STRATEGIES.map((strategy) => (
          <option key={strategy.value} value={strategy.value}>
            {strategy.label}
          </option>
        ))}
      </select>
      {field && (
        <TextField
          label={field.label}
          inputMode="decimal"
          value={draft[field.key]}
          onChange={(value) => {
            onChange({ [field.key]: value });
          }}
        />
      )}
    </label>
  );
}

interface TextFieldProps {
  label: string;
  value: string;
  type?: string;
  inputMode?: "decimal";
  onChange: (value: string) => void;
}

function TextField({
  label,
  value,
  type,
  inputMode,
  onChange,
}: TextFieldProps) {
  return (
    <label>
      {label}
      <input
        required
        type={type ?? "text"}
        inputMode={inputMode}
        value={value}
        onChange={(event: ChangeEvent<HTMLInputElement>) => {
          onChange(event.target.value);
        }}
      />
    </label>
  );
}

function AccountPicker({ accounts, draft, onChange }: GoalFieldsProps) {
  return (
    <fieldset className="goal-accounts">
      <legend>Funding Accounts</legend>
      {accounts.map((account) => (
        <label key={account.id} className="goal-account">
          <input
            type="checkbox"
            checked={draft.accountIds.includes(account.id)}
            onChange={() => {
              onChange({
                ...draft,
                accountIds: toggle(draft.accountIds, account.id),
              });
            }}
          />
          {account.name}
        </label>
      ))}
    </fieldset>
  );
}
