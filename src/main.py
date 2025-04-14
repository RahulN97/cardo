from config.app_config import AppConfig
from agent.broker import Broker
from fox.messenger import Messenger
from alpaca.herder import AlpacaHerder
from parser.message_parser import MessageParser


def initialize_broker(config: AppConfig) -> Broker:
    config: AppConfig = AppConfig.from_environment()
    messenger: Messenger = Messenger(
        user=config.sys_user,
        profile=config.browser_profile,
        lag=config.messenger_lag,
    )
    parser: MessageParser = MessageParser(broker_name=config.broker_name)
    herder: AlpacaHerder = AlpacaHerder(
        broker_name=config.broker_name,
        base_url=config.alpaca_base_url,
        api_key=config.alpaca_api_key,
        api_secret=config.alpaca_api_secret,
    )
    return Broker(
        name=config.broker_name,
        messenger=messenger,
        parser=parser,
        herder=herder,
    )


def run() -> None:
    config: AppConfig = AppConfig.from_environment()
    broker: Broker = initialize_broker(config)
    try:
        broker.run()
    except KeyboardInterrupt:
        broker.stop()


if __name__ == "__main__":
    run()
