import time

from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement

from broker.action import Action
from parser import MessageParser


class Broker:
    def __init__(self, user: str, profile: str, parser: MessageParser) -> None:
        self.parser: MessageParser = parser
        self.driver: Firefox = self._build_driver(user=user, profile=profile)
        self.actions: ActionChains = ActionChains(self.driver)

    def _build_driver(self, user: str, profile: str) -> Firefox:
        options: Options = Options()
        options.profile = (
            f"/Users/{user}/Library/Application Support/Firefox/Profiles/{profile}"
        )
        driver: Firefox = Firefox(options=options)
        driver.get("https://www.messenger.com")
        self._wait()
        return driver

    @staticmethod
    def _wait() -> None:
        time.sleep(2)

    def _get_latest_message(self) -> str | None:
        rows: list[WebElement] = self.driver.find_elements(
            By.CSS_SELECTOR, "div[role='row']"
        )
        if not rows:
            return None

        for row in reversed(rows):
            try:
                text_elem = row.find_element(By.CSS_SELECTOR, "div[dir='auto']")
                text = text_elem.text.strip()
                if text:
                    return text
            except Exception:
                continue

        return None

    def _handle_action(self, action: Action, output_text: str | None) -> str | None:
        match action:
            case Action.NONE:
                return output_text
            case Action.TRADE:
                # trade = self.exchange.submit_trade()
                # resp = self.ledger.record_trade(trade)
                return output_text
            case Action.GET_TRADES:
                # resp = self.ledger.get_trades()
                return output_text
            case Action.GET_DAILY_PNL:
                # resp = self.ledger.get_daily_pnl()
                return output_text
            case Action.GET_PNL:
                # resp = self.ledger.get_pnl()
                return output_text
            case _:
                raise NotImplementedError(f"Cannot handle action: {action}")

    def _reply(self, reply: str) -> None:
        input_box = self.driver.find_element(By.XPATH, "//div[@aria-label='Message']")
        input_box.click()
        self.actions.move_to_element(input_box)
        self.actions.click()
        self.actions.send_keys(reply)
        self.actions.send_keys(Keys.ENTER)
        self.actions.perform()
        self.actions.reset_actions()
        print(f"Replied with: {reply}")

    def run(self) -> None:
        last_message: str = ""

        while True:
            self._wait()

            message: str | None = self._get_latest_message()
            if message is None or message == last_message:
                continue

            print(f"New message: {message}")
            action, output_text = self.parser.parse(message)
            reply = self._handle_action(action, output_text)

            if reply is not None:
                self._reply(reply)
                last_message = reply
            else:
                last_message = message

    def shutdown(self) -> None:
        self.driver.quit()
