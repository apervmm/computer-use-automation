from dataclasses import dataclass, field
from typing import Literal, Optional
from enum import Enum


class LocatorStrategy(str, Enum):
    ROLE_NAME = "role_name"      
    CSS = "css"                 
    TEXT = "text"               
    XPATH = "xpath"          


@dataclass
class ElementRef:
    strategy: LocatorStrategy
    value: str                     
    role: Optional[str] = None     
    fallbacks: list["ElementRef"] = field(default_factory=list)


@dataclass
class InteractiveElement:
    ref: ElementRef
    role: str
    accessible_name: str
    element_type: Literal["button", "link", "textbox", "select", "checkbox", "other"]
    is_visible: bool = True


@dataclass
class PageState:
    """What the agent 'sees' at one point in time."""
    url: str
    title: str
    interactive_elements: list[InteractiveElement]
    visible_text_summary: str      
    screenshot_path: Optional[str] = None   


@dataclass
class ActionResult:
    success: bool
    action: str     # click | type |navigate | read
    target_description: str         # for logs
    error: Optional[str] = None
    duration_ms: int = 0