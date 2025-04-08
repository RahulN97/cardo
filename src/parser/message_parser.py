from agent.profiles import PROFILE_TO_RULES, Rule
from stubs import Request, NoRequest


class MessageParser:
    def __init__(self, broker_name: str) -> None:
        self.rules: list[Rule] = PROFILE_TO_RULES[broker_name]

    def resolve(self, input_message: str) -> tuple[Request, str | None]:
        for rule in self.rules:
            if rule.should_apply_rule(input_message):
                return rule.build_request(input_message), rule.output_message
        return NoRequest(), None
