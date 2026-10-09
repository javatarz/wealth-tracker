import { ALL, type FilterOptions, type Scope } from "./dashboardApi";

export const ALL_MEMBERS = "All Members";
export const ALL_CLASSES = "All Classes";

export interface FilterBarProps {
  filters: FilterOptions;
  scope: Scope;
  onChange: (scope: Scope) => void;
}

export function FilterBar({ filters, scope, onChange }: FilterBarProps) {
  return (
    <div className="filter-bar">
      <label className="filter-field">
        Member
        <select
          value={scope.member}
          onChange={(event) => {
            onChange({ ...scope, member: event.target.value });
          }}
        >
          <option value={ALL}>{ALL_MEMBERS}</option>
          {filters.members.map((member) => (
            <option key={member.id} value={member.id}>
              {member.name}
            </option>
          ))}
        </select>
      </label>
      <label className="filter-field">
        Asset Class
        <select
          value={scope.assetClass}
          onChange={(event) => {
            onChange({ ...scope, assetClass: event.target.value });
          }}
        >
          <option value={ALL}>{ALL_CLASSES}</option>
          {filters.asset_classes.map((entry) => (
            <option key={entry.value} value={entry.value}>
              {entry.label}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
