import json
from pathlib import Path
from .schema import Capability

ARTIFACT_DIR = Path("artifacts")


def save(capability: Capability) -> Path:
    """
    Saves as artifacts/<capability_id>.v<version>.json
    """
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    path = ARTIFACT_DIR / f"{capability.capability_id}.v{capability.version}.json"
    path.write_text(capability.model_dump_json(indent=2))
    return path


def load(capability_id: str, version: int | None = None) -> Capability:
    if version is not None:
        path = ARTIFACT_DIR / f"{capability_id}.v{version}.json"
        return Capability.model_validate_json(path.read_text())

    candidates = sorted(ARTIFACT_DIR.glob(f"{capability_id}.v*.json"))
    if not candidates:
        raise FileNotFoundError(f"No artifact found for {capability_id}")
    return Capability.model_validate_json(candidates[-1].read_text())