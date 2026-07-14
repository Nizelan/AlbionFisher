"""Load ``model/classes.yaml`` and verify it against a loaded model's names.

The YAML file is the single source of truth for class IDs (SPEC §4). At startup
the app compares the model's embedded names with the contract and surfaces any
mismatch as UI warnings — it does not refuse to run.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONTRACT_PATH = Path("model") / "classes.yaml"


class ClassContractError(ValueError):
    """Raised when classes.yaml itself is malformed."""


@dataclass(frozen=True)
class ClassContract:
    nc: int
    names: dict[int, str]


def load_contract(path: "str | Path" = DEFAULT_CONTRACT_PATH) -> ClassContract:
    import yaml  # lazy

    path = Path(path)
    if not path.exists():
        raise ClassContractError(f"class contract not found: {path}")
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict) or "names" not in data:
        raise ClassContractError(f"{path} must be a mapping with a 'names' section")

    raw_names = data["names"]
    if not isinstance(raw_names, dict):
        raise ClassContractError(f"{path}: 'names' must be an id -> name mapping")
    names: dict[int, str] = {}
    for key, value in raw_names.items():
        if not isinstance(key, int) or not isinstance(value, str):
            raise ClassContractError(f"{path}: bad names entry {key!r}: {value!r}")
        names[key] = value

    nc = data.get("nc", len(names))
    if not isinstance(nc, int) or nc != len(names):
        raise ClassContractError(f"{path}: nc={nc!r} does not match {len(names)} names")
    if sorted(names) != list(range(nc)):
        raise ClassContractError(f"{path}: class IDs must be contiguous 0..{nc - 1}")
    return ClassContract(nc=nc, names=names)


def _normalize(model_names: Mapping[int, str] | Sequence[str]) -> dict[int, str]:
    if isinstance(model_names, Mapping):
        return dict(model_names)
    return dict(enumerate(model_names))


def verify(
    contract: ClassContract,
    model_names: Mapping[int, str] | Sequence[str],
) -> list[str]:
    """Compare model class names against the contract; return warning strings."""
    warnings: list[str] = []
    model = _normalize(model_names)

    if len(model) != contract.nc:
        warnings.append(
            f"model has {len(model)} classes, contract expects {contract.nc}"
        )
    for class_id, expected in contract.names.items():
        actual = model.get(class_id)
        if actual is None:
            warnings.append(f"model is missing class {class_id} ({expected})")
        elif actual != expected:
            warnings.append(
                f"class {class_id}: model says '{actual}', contract says '{expected}'"
            )
    for class_id in sorted(set(model) - set(contract.names)):
        warnings.append(
            f"model has extra class {class_id} ('{model[class_id]}') not in contract"
        )
    return warnings
