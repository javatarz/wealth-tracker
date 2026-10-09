"""Why a Goal request was turned away, in terms the browser can show."""

import uuid
from typing import Literal

GoalRejectionCode = Literal[
    "goal_not_found",
    "unknown_accounts",
    "unknown_position",
    "schedule_not_found",
    "invalid_schedule",
]


class GoalRejectedError(Exception):
    def __init__(self, code: GoalRejectionCode, message: str) -> None:
        super().__init__(message)
        self.code: GoalRejectionCode = code
        self.message = message


class GoalNotFoundError(GoalRejectedError):
    def __init__(self, goal_id: uuid.UUID) -> None:
        super().__init__("goal_not_found", f"Goal {goal_id} doesn't exist.")


class UnknownAccountsError(GoalRejectedError):
    def __init__(self) -> None:
        super().__init__("unknown_accounts", "One or more of the chosen Accounts don't exist.")


class UnknownPositionsError(GoalRejectedError):
    def __init__(self) -> None:
        super().__init__("unknown_position", "That Position doesn't exist.")


class ScheduleNotFoundError(GoalRejectedError):
    def __init__(self, schedule_id: uuid.UUID) -> None:
        super().__init__(
            "schedule_not_found", f"Scheduled Transaction {schedule_id} doesn't exist."
        )


class InvalidScheduleError(GoalRejectedError):
    def __init__(self) -> None:
        super().__init__(
            "invalid_schedule",
            "A Scheduled Transaction needs a positive amount and an end date after its start.",
        )
