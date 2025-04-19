class MissingConfigError(Exception):
    ERR_MSG: str = "Missing required config: {key}. Set it in .env file"

    def __init__(self, key: str) -> None:
        super().__init__(self.ERR_MSG.format(key=key))


class ErroredOrderState(Exception):
    ERR_MSG: str = (
        "Something went wrong - order {order_id} is stuck with status {status} "
        "and didn't get filled or canceled within {timeout} seconds. Exiting"
    )

    def __init__(self, order_id: str, status: str, timeout: int) -> None:
        super().__init__(
            self.ERR_MSG.format(order_id=order_id, status=status, timeout=timeout)
        )


class BrokerProfileNotImplemented(Exception):
    ERR_MSG: str = (
        "Broker name {name} does not exist. "
        "Need to implement profile, dialogue, and rules for each character"
    )

    def __init__(self, name: str) -> None:
        super().__init__(self.ERR_MSG.format(name=name))
