import logging

from agent.broker import Broker
from agent.profiles import BROKER_NAME_TO_PROFILE, Profile
from alpaca.herder import AlpacaHerder
from canvas.visualizer import DataVisualizer
from config.app_config import AppConfig
from errors import BrokerProfileNotImplemented
from fox.messenger import Messenger
from resolver.message_resolver import MessageResolver


def setup_env(config: AppConfig) -> None:
    logging.basicConfig(level=config.log_level)


def initialize_broker(config: AppConfig) -> Broker:
    try:
        profile: Profile = BROKER_NAME_TO_PROFILE[config.broker_name]
    except KeyError:
        raise BrokerProfileNotImplemented(name=config.broker_name)

    messenger: Messenger = Messenger(
        user=config.sys_user,
        profile=config.browser_profile,
        lag=config.messenger_lag,
    )
    resolver: MessageResolver = MessageResolver(profile=profile)
    visualizer: DataVisualizer = DataVisualizer(profile=profile)
    herder: AlpacaHerder = AlpacaHerder(
        profile=profile,
        base_url=config.alpaca_base_url,
        api_key=config.alpaca_api_key,
        api_secret=config.alpaca_api_secret,
        visualizer=visualizer,
    )
    return Broker(
        profile=profile,
        messenger=messenger,
        resolver=resolver,
        herder=herder,
    )


def run() -> None:
    config: AppConfig = AppConfig.from_environment()
    setup_env(config)

    broker: Broker = initialize_broker(config)
    broker.start()
    try:
        broker.run()
    except KeyboardInterrupt:
        broker.stop()


if __name__ == "__main__":
    run()
