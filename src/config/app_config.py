import os
from dataclasses import dataclass
from dotenv import load_dotenv

from errors import MissingConfigError
from config.environment import Environment


@dataclass(kw_only=True)
class AppConfig:
    env: Environment
    sys_user: str
    broker_name: str
    browser_profile: str
    messenger_lag: int | None
    alpaca_base_url: str
    alpaca_api_key: str
    alpaca_api_secret: str

    @classmethod
    def from_environment(cls) -> "AppConfig":
        load_dotenv()
        return cls(
            env=Environment.from_str(cls._get_optional("ENV")),
            sys_user=cls._get_required("USER"),
            broker_name=cls._get_required("BROKER_NAME"),
            browser_profile=cls._get_required("BROWSER_PROFILE"),
            messenger_lag=cls._get_optional("MESSENGER_LAG"),
            alpaca_base_url=cls._get_required("ALPACA_BASE_URL"),
            alpaca_api_key=cls._get_required("ALPACA_API_KEY"),
            alpaca_api_secret=cls._get_required("ALPACA_API_SECRET"),
        )

    @staticmethod
    def _get_required(key: str) -> str:
        try:
            return os.environ[key]
        except KeyError:
            raise MissingConfigError(key)

    @staticmethod
    def _get_optional(key: str) -> str | None:
        return os.environ.get(key)
