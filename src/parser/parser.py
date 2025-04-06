from parser.mappings import RULE_MAPPINGS, Rule
from broker.action import Action


class MessageParser:
    def __init__(self, broker_name: str) -> None:
        self.rules: list[Rule] = RULE_MAPPINGS[broker_name]

    def parse(self, input_message: str) -> tuple[Action, str | None]:
        for rule in self.rules:
            if rule.match_fn(input_message):
                return rule.action, rule.output_message
        return Action.NONE, None
