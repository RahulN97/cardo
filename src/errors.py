class MissingConfigError(Exception):
    def __init__(self, key: str) -> None:
        super().__init__(f"Missing required config: {key}. Set it in .env file")
