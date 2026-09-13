import re

# Not exhaustive PII detection
# Goal: never let credentials or account-like numbers persist verbatim into artifacts or logs

_PATTERNS = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED-SSN]"),
    (re.compile(r"\b\d{13,19}\b"), "[REDACTED-CARD-OR-ACCOUNT]"),
]


def redact(text: str) -> str:
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def redact_dict(d: dict, sensitive_keys: set[str] = frozenset({"password", "ssn", "pin"})) -> dict:
    out = {}
    for k, v in d.items():
        if k.lower() in sensitive_keys:
            out[k] = "[REDACTED]"
        elif isinstance(v, str):
            out[k] = redact(v)
        else:
            out[k] = v
    return out