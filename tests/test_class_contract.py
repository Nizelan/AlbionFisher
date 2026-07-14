"""Class contract tests against the real model/classes.yaml (SPEC §4)."""

from pathlib import Path

import pytest

from albionfisher.detection.class_contract import (
    ClassContract,
    ClassContractError,
    load_contract,
    verify,
)
from albionfisher.detection.types import CLASS_NAMES

REAL_CONTRACT = Path(__file__).resolve().parents[1] / "model" / "classes.yaml"

EXPECTED_NAMES = {
    0: "fishing_zone",
    1: "bobber_idle",
    2: "bobber_bite",
    3: "minigame_bar",
    4: "minigame_float",
    5: "minigame_zone",
    6: "catch_popup",
}


def test_real_contract_parses_with_stable_ids():
    contract = load_contract(REAL_CONTRACT)
    assert contract.nc == 7
    assert contract.names == EXPECTED_NAMES


def test_code_constants_match_contract():
    contract = load_contract(REAL_CONTRACT)
    assert contract.names == CLASS_NAMES


def test_matching_model_yields_no_warnings():
    contract = load_contract(REAL_CONTRACT)
    assert verify(contract, EXPECTED_NAMES) == []
    # ultralytics may expose names as a list as well
    assert verify(contract, [EXPECTED_NAMES[i] for i in range(7)]) == []


def test_renamed_class_is_reported():
    contract = load_contract(REAL_CONTRACT)
    model = dict(EXPECTED_NAMES)
    model[2] = "bobber_splash"
    warnings = verify(contract, model)
    assert len(warnings) == 1
    assert "bobber_splash" in warnings[0] and "bobber_bite" in warnings[0]


def test_missing_and_extra_classes_are_reported():
    contract = load_contract(REAL_CONTRACT)
    model = {i: EXPECTED_NAMES[i] for i in range(6)}  # drop catch_popup
    model[7] = "seagull"
    warnings = verify(contract, model)
    assert any("missing class 6" in w for w in warnings)
    assert any("extra class 7" in w for w in warnings)


def test_missing_file_raises():
    with pytest.raises(ClassContractError, match="not found"):
        load_contract(REAL_CONTRACT.parent / "nope.yaml")


def test_non_contiguous_ids_rejected(tmp_path):
    bad = tmp_path / "classes.yaml"
    bad.write_text("nc: 2\nnames:\n  0: a\n  2: b\n", encoding="utf-8")
    with pytest.raises(ClassContractError, match="contiguous"):
        load_contract(bad)


def test_contract_dataclass_is_frozen():
    contract = ClassContract(nc=1, names={0: "x"})
    with pytest.raises(AttributeError):
        contract.nc = 2  # type: ignore[misc]
