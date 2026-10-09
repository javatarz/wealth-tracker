import { formatDecimal } from "../statements/formatDecimal";
import type { DashboardSummary } from "./dashboardApi";

export function ReturnsSummary({ dashboard }: { dashboard: DashboardSummary }) {
  return (
    <section aria-labelledby="returns-heading">
      <h3 id="returns-heading">Returns</h3>
      <table>
        <thead>
          <tr>
            <th scope="col">Metric</th>
            <th scope="col" className="num">
              Amount (₹)
            </th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">Current value</th>
            <td className="num">{formatDecimal(dashboard.current_value)}</td>
          </tr>
          <tr>
            <th scope="row">Total invested</th>
            <td className="num">{formatDecimal(dashboard.invested)}</td>
          </tr>
          <tr>
            <th scope="row">Absolute return</th>
            <td className="num">{formatDecimal(dashboard.absolute_return)}</td>
          </tr>
        </tbody>
      </table>
    </section>
  );
}
