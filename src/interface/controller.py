from typing import Any, Callable
import random
import time

from selenium.webdriver import Firefox
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys


class Controller:
    MIN_WAIT_TIME: float = 0.01
    MAX_WAIT_TIME: float = 0.08

    MAX_X_OFFSET: int = 5
    MAX_Y_OFFSET: int = 15

    def __init__(self, driver: Firefox) -> None:
        self.actions: ActionChains = ActionChains(driver)

    @staticmethod
    def humanize(f: Callable) -> Callable:
        def inner(self: "Controller", *args, **kwargs) -> Any:
            pause_time: float = random.uniform(self.MIN_WAIT_TIME, self.MAX_WAIT_TIME)
            time.sleep(pause_time)
            return f(self, *args, **kwargs)

        return inner

    @humanize
    def _move_to_element(self, element: WebElement, x: int, y: int) -> None:
        self.actions.move_to_element_with_offset(
            to_element=element, xoffset=x, yoffset=y
        )

    @humanize
    def _click(self) -> None:
        self.actions.click()

    @humanize
    def _type_char(self, c: str) -> None:
        self.actions.key_down(c)
        self.actions.key_up(c)

    def click_on_element(self, element: WebElement) -> None:
        self._move_to_element(
            element,
            x=random.randint(0, self.MAX_X_OFFSET),
            y=random.randint(0, self.MAX_Y_OFFSET),
        )
        self._click()

    def type_text(self, text: str) -> None:
        for c in text:
            self._type_char(c)
        self._type_char(Keys.ENTER)
        self.actions.perform()
        self.actions.reset_actions()
