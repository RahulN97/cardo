import logging

from agent.broker import Broker
from agent.profiles import BROKER_NAME_TO_PROFILE, Profile
from alpaca.client import AlpacaClient, get_alpaca_client
from alpaca.exchange import Exchange
from alpaca.herder import AlpacaHerder
from alpaca.ledger import Ledger
from canvas.visualizer import DataVisualizer
from config.app_config import AppConfig
from errors import BrokerProfileNotImplemented
from fox.messenger import Messenger
from resolver.message_resolver import MessageResolver


def setup_env(config: AppConfig) -> None:
    logging.basicConfig(level=config.log_level)


def create_herder(config: AppConfig, profile: Profile) -> AlpacaHerder:
    client: AlpacaClient = get_alpaca_client(
        env=config.env,
        base_url=config.alpaca_base_url,
        api_key=config.alpaca_api_key,
        api_secret=config.alpaca_api_secret,
        test_id=config.alpaca_test_id,
    )
    exchange: Exchange = Exchange(client=client, id=profile.broker_name)
    ledger: Ledger = Ledger(client=client)
    visualizer: DataVisualizer = DataVisualizer(profile=profile)
    return AlpacaHerder(
        env=config.env,
        exchange=exchange,
        ledger=ledger,
        visualizer=visualizer,
    )


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
    herder: AlpacaHerder = create_herder(config=config, profile=profile)
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
