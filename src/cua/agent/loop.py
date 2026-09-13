from dataclasses import dataclass, field
from pathlib import Path

from cua.surface.browser import BrowserSession
from cua.surface.perception import snapshot
from cua.surface.types import PageState, ElementRef

from .llm_client import LLMClient
from .prompts import SYSTEM_PROMPT, TOOLS


@dataclass
class TranscriptStep:
    step_num: int
    page_url: str
    tool_name: str
    tool_input: dict
    success: bool
    detail: str
    screenshot_path: str | None = None
    resolved_ref: ElementRef | None = None 


@dataclass
class AgentRunResult:
    goal: str
    success: bool
    stop_reason: str
    transcript: list[TranscriptStep] = field(default_factory=list)
    outputs: dict = field(default_factory=dict)


class AgentLoop:
    def __init__(self, session: BrowserSession, llm: LLMClient,
                 max_steps: int = 15, evidence_dir: str = "evidence/discovery"):
        self.session = session
        self.llm = llm
        self.max_steps = max_steps
        self.evidence_dir = evidence_dir
        Path(evidence_dir).mkdir(parents=True, exist_ok=True)

    def run(self, goal: str, start_url: str) -> AgentRunResult:
        self.session.goto(start_url)
        transcript: list[TranscriptStep] = []
        outputs: dict = {}

        state = snapshot(self.session, screenshot_path=f"{self.evidence_dir}/step_0.png")
        messages = [{"role": "user", "content": self._observation_text(goal, state)}]

        for step_num in range(1, self.max_steps + 1):
            response = self.llm.decide(messages, SYSTEM_PROMPT, TOOLS)
            tool_use = next((b for b in response.content if b.type == "tool_use"), None)

            if tool_use is None:
                return AgentRunResult(goal, False, "no_tool_call", transcript, outputs)

            messages.append({"role": "assistant", "content": response.content})

            if tool_use.name == "done":
                outputs = tool_use.input.get("outputs", {})
                transcript.append(TranscriptStep(
                    step_num, state.url, "done", tool_use.input, True, "goal completed"))
                return AgentRunResult(goal, True, "goal_met", transcript, outputs)

            result_text, state, ref= self._execute(tool_use, state, step_num)

            success = "ERROR" not in result_text
            transcript.append(TranscriptStep(
                step_num, 
                state.url, 
                tool_use.name, 
                tool_use.input, 
                success, 
                result_text,
                screenshot_path=f"{self.evidence_dir}/step_{step_num}.png",
                resolved_ref=ref
            ))

            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result_text,
                }],
            })

        return AgentRunResult(goal, False, "max_steps_exceeded", transcript, outputs)

    def _execute(
        self, 
        tool_use, 
        state: PageState, 
        step_num: int
    ) -> tuple[str, PageState, ElementRef | None]:
        name, inp = tool_use.name, tool_use.input

        if name == "click":
            ref = state.find_ref(inp["element_name"], inp.get("role"))
            if ref is None:
                return f"ERROR: no element named '{inp['element_name']}' found on this page.",  state, None
            result = self.session.click(ref, description=inp["element_name"])
        elif name == "type_text":
            ref = state.find_ref(inp["element_name"], "textbox")
            if ref is None:
                return f"ERROR: no textbox named '{inp['element_name']}' found on this page.",  state, None
            result = self.session.type_text(ref, inp["text"], description=inp["element_name"])
        elif name == "navigate":
            ref = None
            result = self.session.goto(inp["url"])
        elif name == "read":
            ref = None
            element_name = inp.get("element_name")
            if element_name:
                ref = state.find_ref(element_name)
            return f"Recorded {inp['label']} = {inp['value']}.", state, ref
        else:
            return f"ERROR: unknown tool '{name}'.", state, None

        new_state = snapshot(self.session, screenshot_path=f"{self.evidence_dir}/step_{step_num}.png")
        if not result.success:
            return f"ERROR: {name} failed — {result.error}", new_state, ref
        return f"{name} succeeded. New page: {self._observation_text(None, new_state, include_goal=False)}", new_state, ref


    def _observation_text(self, goal: str | None, state: PageState, include_goal: bool = True) -> str:
        elements = "\n".join(
            f"- [{el.role}] '{el.accessible_name}'" for el in state.interactive_elements
        )
        parts = []
        if include_goal and goal:
            parts.append(f"GOAL: {goal}\n")
        parts.append(f"Current URL: {state.url}\nPage title: {state.title}")
        parts.append(f"Interactive elements:\n{elements}")
        parts.append(f"Visible text (truncated): {state.visible_text_summary[:500]}")
        return "\n\n".join(parts)