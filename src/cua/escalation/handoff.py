
from enum import Enum
from datetime import datetime, timezone
from dataclasses import dataclass, field



class EscalationReason(str, Enum):
    DISCOVERY_STUCK = "discovery_stuck" # hitting max step, no tooling, or dead-end
    REPLAY_FAILURE = "replay_failure"      # unrecoverable replay failure
    RISKY_CONFIRMATION = "risky_confirmation" 


@dataclass
class EscalationRequest:
    reason: EscalationReason
    capability_or_goal: str
    current_step: int
    current_url: str
    detail: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class HandoffState:
    def __init__(self):
        self.automation_in_control = True
        self.human_actions_log: list[str] = []

    def transfer_to_human(self):
        self.automation_in_control = False

    def resume_automation(self):
        self.automation_in_control = True

    def record_human_action(self, description: str):
        self.human_actions_log.append(description)

