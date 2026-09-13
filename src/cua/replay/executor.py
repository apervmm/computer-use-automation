import re
from cua.surface.browser import BrowserSession
from cua.surface.perception import snapshot
from cua.artifact.schema import Capability, StepAction, Checkpoint, OutcomeRule
from .outcomes import ReplayResult, ReplayStatus


def replay(session: BrowserSession, capability: Capability, inputs: dict) -> ReplayResult:
    """
    Execute a saved Capability deterministically, using the provided inputs to fill in any parameterized values.
    
    Checkpoint miss => checks declared outcome_rules before concluding it's a hard failure.
    """
    _validate_inputs(capability, inputs)

    session.goto(capability.entry_url)

    for step in capability.steps:
        value = _substitute(step.value, inputs) if step.value else None

        if step.action == StepAction.NAVIGATE:
            result = session.goto(value)
        elif step.action == StepAction.CLICK:
            result = session.click(step.target, description=step.description)
        elif step.action == StepAction.TYPE_TEXT:
            result = session.type_text(step.target, value, description=step.description)
        else:
            continue  # READ steps don't act on the browser

        if not result.success:
            outcome = _check_outcomes(session, capability.outcome_rules)
            if outcome:
                return ReplayResult(
                    status=ReplayStatus.BUSINESS_OUTCOME,
                    capability_id=capability.capability_id,
                    outcome_name=outcome,
                )
            return ReplayResult(
                status=ReplayStatus.FAILURE,
                capability_id=capability.capability_id,
                failed_step=step.step_num,
                expected=step.description,
                observed=result.error,
                error=f"Step {step.step_num} ({step.action}) failed: {result.error}",
            )
        
    if capability.checkpoint and not _checkpoint_met(session, capability.checkpoint):
        outcome = _check_outcomes(session, capability.outcome_rules)
        if outcome:
            return ReplayResult(
                status=ReplayStatus.BUSINESS_OUTCOME,
                capability_id=capability.capability_id,
                outcome_name=outcome,
            )
        return ReplayResult(
            status=ReplayStatus.FAILURE,
            capability_id=capability.capability_id,
            failed_step=capability.steps[-1].step_num if capability.steps else None,
            expected=f"{capability.checkpoint.kind}={capability.checkpoint.expected}",
            observed=session.page.url,
            error="Checkpoint not met and no matching business outcome found.",
        )

    outputs = _extract_outputs(session, capability)
    return ReplayResult(status=ReplayStatus.SUCCESS, capability_id=capability.capability_id, outputs=outputs)


def _validate_inputs(capability: Capability, inputs: dict) -> None:
    missing = [p.name for p in capability.inputs if p.required and p.name not in inputs]
    if missing:
        raise ValueError(f"Missing required input(s): {missing}")


def _substitute(template: str, inputs: dict) -> str:
    """Replace every {param_name} in a step's value with the supplied input"""
    def _sub(match):
        key = match.group(1)
        if key not in inputs:
            raise ValueError(f"Step references unknown param '{{{key}}}'")
        return str(inputs[key])
    return re.sub(r"\{(\w+)\}", _sub, template)


def _checkpoint_met(session: BrowserSession, checkpoint: Checkpoint) -> bool:
    if checkpoint.kind == "url_contains":
        return checkpoint.expected in session.page.url
    if checkpoint.kind == "text_visible":
        return checkpoint.expected in session.page.inner_text("body")
    if checkpoint.kind == "element_visible":
        return session.page.locator(checkpoint.expected).first.is_visible()
    return False


def _check_outcomes(session: BrowserSession, rules: list[OutcomeRule]) -> str | None:
    session.page.wait_for_timeout(500)  
    page_text = session.page.inner_text("body")
    for rule in rules:
        if rule.kind == "text_visible" and rule.expected in page_text:
            return rule.name
        if rule.kind == "url_contains" and rule.expected in session.page.url:
            return rule.name
    return None


def _extract_outputs(session: BrowserSession, capability: Capability) -> dict:
    page_text = session.page.inner_text("body")
    outputs = {}
    for field in capability.outputs:
        if "succeed" in field.name.lower() or "success" in field.name.lower():
            outputs[field.name] = "true" 
        else:
            welcome_line = next((l for l in page_text.splitlines() if "Welcome" in l), None)
            outputs[field.name] = welcome_line or page_text[:200]
    return outputs