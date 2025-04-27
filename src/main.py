import logging

from agent.broker import Broker
from agent.character import LlmCharacter
from alpaca.client import AlpacaClient, get_alpaca_client
from alpaca.exchange import Exchange
from alpaca.herder import AlpacaHerder
from alpaca.ledger import Ledger
from canvas.visualizer import DataVisualizer
from config.app_config import AppConfig
from fox.messenger import Messenger


def setup_env(config: AppConfig) -> None:
    logging.basicConfig(level=config.log_level)


def create_herder(config: AppConfig, name: str) -> AlpacaHerder:
    client: AlpacaClient = get_alpaca_client(
        env=config.env,
        base_url=config.alpaca_base_url,
        api_key=config.alpaca_api_key,
        api_secret=config.alpaca_api_secret,
        test_id=config.alpaca_test_id,
    )
    exchange: Exchange = Exchange(client=client, name=name)
    ledger: Ledger = Ledger(client=client)
    visualizer: DataVisualizer = DataVisualizer(name=name)
    return AlpacaHerder(
        env=config.env,
        exchange=exchange,
        ledger=ledger,
        visualizer=visualizer,
    )


def initialize_broker(config: AppConfig) -> Broker:
    messenger: Messenger = Messenger(
        user=config.sys_user,
        profile=config.browser_profile,
        lag=config.messenger_lag,
    )
    character: LlmCharacter = LlmCharacter(
        name=config.broker_name,
        openai_api_key=config.openai_api_key,
        model=config.openai_model,
        temperature=config.openai_temperature,
    )
    herder: AlpacaHerder = create_herder(config=config, name=config.broker_name)
    return Broker(
        name=config.broker_name,
        messenger=messenger,
        character=character,
        herder=herder,
        max_lag=config.max_broker_lag,
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
