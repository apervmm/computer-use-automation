
from enum import Enum



class EscalationReason(str, Enum):
    DISCOVERY_STUCK = "discovery_stuck" # hitting max step, no tooling, or dead-end
    REPLAY_FAILURE = "replay_failure"      # unrecoverable replay failure
    RISKY_CONFIRMATION = "risky_confirmation" 