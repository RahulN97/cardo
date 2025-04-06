import re
from dataclasses import dataclass
from typing import Callable

from broker.action import Action


@dataclass(kw_only=True)
class Rule:
    match_fn: Callable[[str], bool]
    action: Action
    output_message: str


RULE_MAPPINGS: dict[str, list[Rule]] = {
    "cardo": [
        Rule(
            match_fn=lambda s: bool(re.fullmatch(r"(?i)cardo+", s)),
            action=Action.TRADE,
            output_message="Your dinner's ready!",
        )
    ],
}
