from agent.profiles import Profile
from agent.rules import Rule
from stubs import NullRequest, Request


class MessageResolver:
    def __init__(self, profile: Profile) -> None:
        self.rules: list[Rule] = profile.rules

    def match(self, input_message: str) -> tuple[Request, str | None]:
        for rule in self.rules:
            if rule.should_apply_rule(input_message):
                return rule.build_request(input_message), rule.output_message
        return NullRequest(), None
