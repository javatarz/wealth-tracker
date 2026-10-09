import type { ChangeEvent } from "react";

import { toggle, type GoalDraft } from "./goalDraft";
import type { AccountSummary } from "./listGoals";

interface GoalFieldsProps {
  draft: GoalDraft;
  accounts: AccountSummary[];
  onChange: (draft: GoalDraft) => void;
}

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
      <AccountPicker accounts={accounts} draft={draft} onChange={onChange} />
    </>
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
