import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { components } from "../api/schema";
import { formatDecimal } from "../statements/formatDecimal";

type ScheduleView = components["schemas"]["ScheduleView"];
type ScheduleBoard = components["schemas"]["ScheduleBoard"];

export function ScheduleList({ goalId }: { goalId: string }) {
  const [schedules, setSchedules] = useState<ScheduleView[]>([]);

  useEffect(() => {
    void fetchSchedules(goalId).then(setSchedules);
  }, [goalId]);

  return schedules.length === 0 ? null : (
    <div className="schedule-list">
      <h4>Scheduled transactions</h4>
      <ul>
        {schedules.map((schedule) => (
          <li key={schedule.id}>
            {schedule.description} · {schedule.frequency} · ₹
            {formatDecimal(schedule.amount)}
            {escalation(schedule)}
          </li>
        ))}
      </ul>
    </div>
  );
}

function escalation(schedule: ScheduleView): string {
  return Number(schedule.escalation_rate) === 0
    ? ""
    : ` · escalating ${schedule.escalation_rate}/yr`;
}

async function fetchSchedules(goalId: string): Promise<ScheduleView[]> {
  try {
    const { data } = await api.GET(
      "/api/goals/{goal_id}/scheduled-transactions",
      { params: { path: { goal_id: goalId } } },
    );
    return (data as ScheduleBoard | undefined)?.schedules ?? [];
  } catch {
    return [];
  }
}
