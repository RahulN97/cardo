from enum import Enum, auto


class Environment(Enum):
    TEST = auto()  # trades using fake alpaca client
    DEV = auto()  # trades on paper account
    PROD = auto()  # trades on live account

    @classmethod
    def from_str(cls, env_str: str | None) -> "Environment":
        if env_str is None:
            return cls.DEV

        match env_str:
            case "test":
                return cls.TEST
            case "prod":
                return cls.PROD
            case _:
                return cls.DEV
