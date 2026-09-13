from .handoff import EscalationRequest


def to_operator(request: EscalationRequest) -> None:
    print(f"Reason: {request.reason.value}")
    print(f"Task: {request.capability_or_goal}")
    print(f"Step:  {request.current_step}")
    print(f"Current URL: {request.current_url}")
    print(f"Detail: {request.detail}")


