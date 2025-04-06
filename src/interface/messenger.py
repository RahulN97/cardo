import time

from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement


DEFAULT_LAG: int = 2
PROFILE_PATH: str = (
    "/Users/{user}/Library/Application Support/Firefox/Profiles/{profile}"
)


class Messenger:
    def __init__(self, user: str, profile: str, lag: int | None = None) -> None:
        self.lag: int = lag or DEFAULT_LAG
        self.driver: Firefox = self._build_driver(user=user, profile=profile)
        self.actions: ActionChains = ActionChains(self.driver)

    def _build_driver(self, user: str, profile: str) -> Firefox:
        options: Options = Options()
        options.profile = PROFILE_PATH.format(user=user, profile=profile)
        driver: Firefox = Firefox(options=options)
        driver.get("https://www.messenger.com")
        self.wait()
        return driver

    def wait(self) -> None:
        time.sleep(self.lag)

    def get_latest_message(self) -> str | None:
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

    def reply(self, text: str) -> None:
        input_box = self.driver.find_element(By.XPATH, "//div[@aria-label='Message']")
        input_box.click()
        self.actions.move_to_element(input_box)
        self.actions.click()
        self.actions.send_keys(text)
        self.actions.send_keys(Keys.ENTER)
        self.actions.perform()
        self.actions.reset_actions()
        print(f"Replied with: {text}")

    def shutdown(self) -> None:
        self.driver.quit()
