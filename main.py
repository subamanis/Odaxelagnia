from selenium import webdriver
from selenium.webdriver.edge.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from typing import Callable

USERNAME = 'petros21'
PASSWORD = 'Smallville21'
EDGE_DRIVER_PATH = 'msedgedriver.exe'


def run():
    driver = webdriver.Edge(executable_path=EDGE_DRIVER_PATH)
    driver.get('https://s37-en.bitefight.gameforge.com/profile')
    login(driver)



def login(driver: WebDriver):
    try:
        username_field = driver.find_element_by_name('user')
    except Exception:
        return

    fill_input(username_field, USERNAME)
    fill_input(driver.find_element_by_name('pass'), PASSWORD)
    driver.find_element_by_class_name('btn-small').click()


def fill_input(_input: WebElement, text: str):
    _input.click()
    _input.send_keys(text)


def get_action(x: int) -> Callable[[WebDriver], None]:
    if x > 2:
        return login
    else:
        return action1


def action1(driver: WebDriver):
    print('actionn')


if __name__ == '__main__':
    run()
