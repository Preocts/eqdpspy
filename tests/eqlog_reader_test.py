from datetime import datetime

import pytest

import eqlog_reader


def test_split() -> None:
    combat_log = "[Tue Apr 12 13:09:04 2022] You hit a defender of fire for 1110 points of disease damage by Strike of Disease II. (Critical)"  # noqa
    expected_ts = datetime(2022, 4, 12, 13, 9, 4)
    expected_chat = "You hit a defender of fire for 1110 points of disease damage by Strike of Disease II. (Critical)"  # noqa

    ts, chat = eqlog_reader.split_log(combat_log)

    assert ts == expected_ts
    assert chat == expected_chat


def test_split_raise() -> None:
    with pytest.raises(eqlog_reader.InvalidLine):
        eqlog_reader.split_log("This is a failed test")


def test_build_model_combat_with_skills() -> None:
    expected_ts = datetime(2022, 4, 12, 13, 9, 4)
    combat_line = "You hit a defender of fire for 1110 points of disease damage by Strike of Disease II. (Critical)"  # noqa
    expected = {
        "time_stamp": expected_ts,
        "combat_type": eqlog_reader.CombatType.COMBAT,
        "verb": "hit",
        "target": "a defender of fire",
        "amount": 1110,
        "skills": "Critical",
        "hitby": "Strike of Disease II",
    }

    result = eqlog_reader.build_model(expected_ts, combat_line)

    for key, value in expected.items():
        assert getattr(result, key) == value, f"{key} - {value}"


def test_build_model_combat_no_skill() -> None:
    expected_ts = datetime(2022, 4, 12, 13, 9, 4)
    combat_line = "You hit a defender of fire for 1110 points of damage."
    expected = {
        "time_stamp": expected_ts,
        "combat_type": eqlog_reader.CombatType.COMBAT,
        "verb": "hit",
        "target": "a defender of fire",
        "amount": 1110,
        "skills": "",
        "hitby": "melee",
    }

    result = eqlog_reader.build_model(expected_ts, combat_line)

    for key, value in expected.items():
        assert getattr(result, key) == value, f"{key} - {value}"


def test_build_model_damage_shield() -> None:
    expected_ts = datetime(2022, 4, 12, 13, 9, 4)
    combat_line = (
        "Halon of Marr is pierced by YOUR thorns for 60 points of non-melee damage."
    )
    expected = {
        "time_stamp": expected_ts,
        "combat_type": eqlog_reader.CombatType.COMBAT_DS,
        "verb": "pierced",
        "target": "Halon of Marr",
        "amount": 60,
        "skills": "",
        "hitby": "thorns",
    }

    result = eqlog_reader.build_model(expected_ts, combat_line)

    for key, value in expected.items():
        assert getattr(result, key) == value, f"{key} - {value}"


def test_ignore_heals() -> None:
    case = "You have been healed for 273 hit points by Aura of Rodcet Effect Rk.III."  # noqa
    expected_ts = datetime(2022, 4, 12, 13, 9, 4)
    expected = {
        "time_stamp": expected_ts,
        "combat_type": eqlog_reader.CombatType.UNKNOWN,
        "verb": "",
        "target": "",
        "amount": 0,
        "skills": "",
        "hitby": "",
    }

    result = eqlog_reader.build_model(expected_ts, case)

    for key, value in expected.items():
        assert getattr(result, key) == value, f"{key} - {value}"
