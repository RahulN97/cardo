import os
from dataclasses import dataclass
from dotenv import load_dotenv

from errors import MissingConfigError


@dataclass(kw_only=True)
class AppConfig:
    user: str
    broker_name: str
    browser_profile: str

    @classmethod
    def from_environment(cls) -> "AppConfig":
        load_dotenv()
        return cls(
            user=cls._get("USER"),
            broker_name=cls._get("BROKER_NAME"),
            browser_profile=cls._get("BROWSER_PROFILE"),
        )

    @staticmethod
    def _get(key: str) -> str:
        try:
            return os.environ[key]
        except KeyError:
            raise MissingConfigError(key)
