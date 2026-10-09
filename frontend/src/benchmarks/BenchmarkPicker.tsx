import type { BenchmarkDefinition } from "./benchmarkConfig";

export function BenchmarkPicker({
  value,
  available,
  disabled = false,
  emptyLabel,
  onChange,
}: {
  value: string;
  available: BenchmarkDefinition[];
  disabled?: boolean;
  emptyLabel?: string;
  onChange: (key: string) => void;
}) {
  return (
    <select
      value={value}
      disabled={disabled}
      onChange={(event) => {
        onChange(event.target.value);
      }}
    >
      {emptyLabel !== undefined && <option value="">{emptyLabel}</option>}
      {available.map((definition) => (
        <option key={definition.key} value={definition.key}>
          {definition.name}
        </option>
      ))}
    </select>
  );
}
