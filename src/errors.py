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


class ContextParsingError(Exception):
    ERR_MSG: str = "Failed to parse character context: {e}"

    def __init__(self, e: str) -> None:
        super().__init__(self.ERR_MSG.format(e=e))


class UnexpectedGptResponse(Exception):
    ERR_MSG: str = "ChatGPT returned an unexpected response: {resp}"

    def __init__(self, resp: str) -> None:
        super().__init__(self.ERR_MSG.format(resp=resp))
