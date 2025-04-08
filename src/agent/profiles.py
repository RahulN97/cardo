from agent.rule import Rule, Cardo_TradeVOO


PROFILE_TO_RULES: dict[str, list[Rule]] = {
    "cardo": [Cardo_TradeVOO()],
}
