import { formatDecimal } from "../statements/formatDecimal";
import type { DashboardPosition, DashboardSummary } from "./dashboardApi";

export interface SummaryTableProps {
  dashboard: DashboardSummary;
  onSelectPosition: (position: DashboardPosition) => void;
}

export function SummaryTable({
  dashboard,
  onSelectPosition,
}: SummaryTableProps) {
  return (
    <table>
      <thead>
        <tr>
          <th scope="col">Scheme</th>
          <th scope="col">Account</th>
          <th scope="col" className="num">
            Current value (₹)
          </th>
          <th scope="col" className="num">
            % of portfolio
          </th>
        </tr>
      </thead>
      <tbody>
        {dashboard.positions.map((position) => (
          <SummaryRow
            key={position.id}
            position={position}
            onSelect={() => {
              onSelectPosition(position);
            }}
          />
        ))}
      </tbody>
    </table>
  );
}

function SummaryRow({
  position,
  onSelect,
}: {
  position: DashboardPosition;
  onSelect: () => void;
}) {
  return (
    <tr onClick={onSelect}>
      <th scope="row">
        <button
          type="button"
          className="link"
          onClick={(event) => {
            event.stopPropagation();
            onSelect();
          }}
        >
          {position.scheme}
        </button>
      </th>
      <td>{position.account}</td>
      <td className="num">{formatDecimal(position.current_value)}</td>
      <td className="num">{formatDecimal(position.percent)}%</td>
    </tr>
  );
}
