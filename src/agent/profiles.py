from dataclasses import dataclass

from agent.rules import Cardo_TradeVOO, Rule


@dataclass(kw_only=True, frozen=True)
class CharacterDialogue:
    init_message: str
    shutdown_message: str
    random_phrases: list[str]
    # TODO: can expand with happy phrases, sad phrases, etc.


@dataclass(kw_only=True, frozen=True)
class Profile:
    broker_name: str
    rules: list[Rule]
    dialogue: CharacterDialogue


_CARDO_PROFILE: Profile = Profile(
    broker_name="cardo",
    rules=[
        Cardo_TradeVOO(),
    ],
    dialogue=CharacterDialogue(
        init_message="Hey, I'm Cardooooo! And I'm ready for your requests",
        shutdown_message="Time for bed :)",
        random_phrases=[],
    ),
)

BROKER_NAME_TO_PROFILE: dict[str, Profile] = {
    "cardo": _CARDO_PROFILE,
}
