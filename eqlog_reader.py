# import numpy
import re
import time
from dataclasses import dataclass
from datetime import datetime
from enum import auto
from enum import Enum
from pathlib import Path

import pandas

LOG_FILE = Path("temp_log")
LINE_GROUPS = re.compile(r"^\[(?P<time>.+?)]\s(?P<log>.+?)$")
DATETIME_PSTR = "%a %b %d %H:%M:%S %Y"
COMBAT_ACTION = re.compile(
    pattern=r"^(?P<who>\w+?) (?P<verb>\w+?) (?P<target>.+?) for (?P<amount>[0-9]+).+$",
    flags=re.IGNORECASE,
)
HIT_SOURCE = re.compile(
    pattern=r"damage by (?P<hitby>.+)\.",
    flags=re.IGNORECASE,
)
COMBAT_SKILL = re.compile(
    pattern=r"\((?P<skills>.+)\)",
    flags=re.IGNORECASE,
)
MELEE_DAMAGE = re.compile(
    pattern="^a (?P<source>.+?) hits YOU for (?P<amount>[0-9]+).*$",
    flags=re.IGNORECASE,
)
DAMAGE_SHIELD = re.compile(
    pattern="^(?P<target>.+?) is (?P<verb>.+?) by YOUR (?P<hitby>.+?) for (?P<amount>[0-9]+) points.+$",  # noqa
    flags=re.IGNORECASE,
)


class InvalidLine(ValueError):
    def __init__(self, chat_line: str, message: str) -> None:
        self.chat_line = chat_line
        self.message = message
        super().__init__(message)


class CombatType(Enum):
    """Enum for combat types."""

    UNKNOWN = auto()
    COMBAT = auto()
    COMBAT_DS = auto()
    DAMAGE = auto()


@dataclass
class CombatModel:
    """Parsed data from combat log."""

    time_stamp: datetime = datetime.now()
    combat_type: CombatType = CombatType.UNKNOWN
    who: str = ""
    verb: str = ""
    target: str = ""
    amount: int = 0
    skills: str = ""
    hitby: str = ""


def build_model(time: datetime, line: str) -> CombatModel:
    """Build a CombatModel from a log line."""
    model = CombatModel(time_stamp=time)
    combat_match = COMBAT_ACTION.match(line)
    ds_match = DAMAGE_SHIELD.match(line)
    melee_damage = MELEE_DAMAGE.match(line)

    if combat_match:
        hitby = HIT_SOURCE.search(line)
        skills = COMBAT_SKILL.search(line)

        model.combat_type = CombatType.COMBAT
        model.who = combat_match.group(1)
        model.verb = combat_match.group(2)
        model.target = combat_match.group(3)
        model.amount = int(combat_match.group(4))
        model.skills = skills.group(1) if skills else ""
        model.hitby = hitby.group(1) if hitby else "melee"

    if ds_match:
        model.combat_type = CombatType.COMBAT_DS
        model.who = "You"
        model.target = ds_match.group(1)
        model.verb = ds_match.group(2)
        model.hitby = ds_match.group(3)
        model.amount = int(ds_match.group(4))

    if melee_damage:
        model.combat_type = CombatType.DAMAGE
        model.who = "You"
        model.target = melee_damage.group(1)
        model.amount = int(melee_damage.group(2))

    return model


def split_log(line: str) -> tuple[datetime, str]:
    """Split log line into datetime and chat text."""
    combat_match = LINE_GROUPS.match(line)
    if not combat_match:
        raise InvalidLine(line, "Could not split line, invalid format")

    timestamp = datetime.strptime(combat_match.group(1), DATETIME_PSTR)
    game_text = combat_match.group(2)

    return timestamp, game_text


if __name__ == "__main__":
    tic = time.perf_counter()

    models: list[CombatModel] = []

    with LOG_FILE.open() as infile:
        for idx, line in enumerate(infile):
            if not (combat_match := LINE_GROUPS.match(line)):
                continue
            timestamp = datetime.strptime(combat_match.group(1), DATETIME_PSTR)
            game_text = combat_match.group(2)
            models.append(build_model(timestamp, game_text))

    dataset = pandas.DataFrame(models)
    print(dataset)
    print(dataset[dataset["combat_type"].isin([CombatType.COMBAT])])
    print(dataset[dataset["combat_type"].isin([CombatType.COMBAT_DS])])

    dataset.to_csv(Path("temp_csv").open("w"))

    toc = time.perf_counter()
    print("runtime:", toc - tic)
