from config import AppConfig
from broker import Broker
from parser import MessageParser


def initialize_broker(config: AppConfig) -> Broker:
    config: AppConfig = AppConfig.from_environment()
    parser: MessageParser = MessageParser(broker_name=config.broker_name)
    return Broker(
        user=config.user,
        profile=config.browser_profile,
        parser=parser,
    )


def run() -> None:
    config: AppConfig = AppConfig.from_environment()
    broker: Broker = initialize_broker(config)
    try:
        broker.run()
    except KeyboardInterrupt:
        broker.shutdown()


if __name__ == "__main__":
    run()
