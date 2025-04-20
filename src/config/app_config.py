import os
from dataclasses import dataclass

from dotenv import load_dotenv

from config.environment import Environment
from errors import MissingConfigError


def env_get(key: str, required: bool = True) -> str | None:
    if not required:
        return os.environ.get(key)
    try:
        return os.environ[key]
    except KeyError:
        raise MissingConfigError(key)


@dataclass(kw_only=True)
class AppConfig:
    env: Environment
    sys_user: str
    broker_name: str
    browser_profile: str
    alpaca_base_url: str
    alpaca_api_key: str
    alpaca_api_secret: str
    alpaca_test_id: str | None
    log_level: str = "INFO"
    messenger_lag: int = 7

    @classmethod
    def from_environment(cls) -> "AppConfig":
        load_dotenv()

        env: Environment = Environment.from_str(env_get("ENV", required=False))
        return cls(
            env=env,
            sys_user=env_get("USER"),
            broker_name=env_get("BROKER_NAME"),
            browser_profile=env_get("BROWSER_PROFILE"),
            alpaca_base_url=env_get("ALPACA_BASE_URL"),
            alpaca_api_key=env_get("ALPACA_API_KEY"),
            alpaca_api_secret=env_get("ALPACA_API_SECRET"),
            alpaca_test_id=env_get("ALPACA_TEST_ID", required=env == Environment.TEST),
            log_level=env_get("LOG_LEVEL", required=False) or cls.log_level,
            messenger_lag=(
                int(env_get("MESSENGER_LAG", required=False) or cls.messenger_lag)
            ),
        )
