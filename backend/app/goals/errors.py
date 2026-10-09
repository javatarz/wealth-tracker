"""Why a Goal request was turned away, in terms the browser can show."""

import uuid
from typing import Literal

GoalRejectionCode = Literal["goal_not_found", "unknown_accounts"]


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
