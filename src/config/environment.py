from enum import Enum, auto


class Environment(Enum):
    DEV = auto()
    PROD = auto()

    @classmethod
    def from_str(cls, inp: str | None) -> "Environment":
        if inp is not None and inp.lower() == "prod":
            return cls.PROD
        return cls.DEV
