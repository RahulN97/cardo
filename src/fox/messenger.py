import random
import time
from dataclasses import dataclass

from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from fox.controller import Controller


@dataclass(kw_only=True)
class ChatResponse:
    message: str
    img_path: str | None


DEFAULT_LAG: int = 10
LAG_JITTER: int = 2
MIN_SCAN_TIME: int = 3
PROFILE_PATH: str = (
    "/Users/{user}/Library/Application Support/Firefox/Profiles/{profile}"
)


class Messenger:
    def __init__(self, user: str, profile: str, lag: int | None = None) -> None:
        self.lag: int = lag or DEFAULT_LAG
        assert self.lag - LAG_JITTER >= MIN_SCAN_TIME
        self.driver: Firefox = self._build_driver(user=user, profile=profile)
        self.controller: Controller = Controller(self.driver)

    def _build_driver(self, user: str, profile: str) -> Firefox:
        options: Options = Options()
        options.profile = PROFILE_PATH.format(user=user, profile=profile)
        driver: Firefox = Firefox(options=options)
        driver.get("https://www.messenger.com")
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        self.wait()
        return driver

    def wait(self) -> None:
        scan_wait: float = random.uniform(self.lag - LAG_JITTER, self.lag + LAG_JITTER)
        time.sleep(scan_wait)

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

    def respond(self, response: ChatResponse) -> None:
        if response.img_path is not None:
            self.send_image(response.img_path)
        self.reply(response.message)

    def send_image(self, img_path: str) -> None:
        file_input = self.driver.find_element(By.XPATH, "//input[@type='file']")
        file_input.send_keys(img_path)

        input_box = self.driver.find_element(By.XPATH, "//div[@aria-label='Message']")
        input_box.click()
        self.controller.click_on_element(input_box)
        self.controller.type_text("")

    def reply(self, text: str) -> None:
        input_box = self.driver.find_element(By.XPATH, "//div[@aria-label='Message']")
        input_box.click()

        self.controller.click_on_element(input_box)
        self.controller.type_text(text)
        print(f"Replied with: {text}")

    def shutdown(self) -> None:
        self.driver.quit()
