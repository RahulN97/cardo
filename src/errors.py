class MissingConfigError(Exception):
    def __init__(self, key: str) -> None:
        super().__init__(f"Missing required config: {key}. Set it in .env file")


class ErroredOrderState(Exception):
    def __init__(self, order_id: str, timeout: int):
        super().__init__(
            f"Something went wrong - order {order_id} failed to cancel within {timeout} seconds. Exiting"
        )
