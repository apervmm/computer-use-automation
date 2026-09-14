from .handoff import EscalationRequest, HandoffState


def to_operator(request: EscalationRequest, state: HandoffState) -> None:
    print(f"Reason: {request.reason.value}")
    print(f"Task: {request.capability_or_goal}")
    print(f"Step:  {request.current_step}")
    print(f"Current URL: {request.current_url}")
    print(f"Detail: {request.detail}")

 
    action_note = input("Describe what you did [or press Enter to skip, then hit Enter to resume]: ")
    if action_note.strip():
        state.record_human_action(action_note.strip())
    
    state.resume_automation()
    print("Resuming...\n")