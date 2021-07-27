from selenium import webdriver
from selenium.webdriver.edge.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from typing import Callable, Any, List

USERNAME = 'petros21'
PASSWORD = 'Smallville21'
EDGE_DRIVER_PATH = 'msedgedriver.exe'
PAGE_URL = 'https://s37-en.bitefight.gameforge.com/profile'


class Action:
    def __init__(self, func: Callable[[WebDriver], None], optional_sub_category: Any, amount: int):
        self.func = func
        self.optional_sub_category = optional_sub_category
        self.amount = amount

    def execute(self):
        self.func(driver)


driver = webdriver.Edge(executable_path=EDGE_DRIVER_PATH)
actions: List[Action] = []


def run():
    show_actions()
    get_input()
    actions[0].execute()
    # driver.get(PAGE_URL)
    # login(driver)


def show_actions():
    print('format: <action_num> <optional_sub_category_num> <amount_num>')
    print('1. Hunt\n'
          '       1. ManHunt 2. Village 3. Small Town 4. City\n'
          '2. Story (1 = 40 story actions)\n'
          '3. Graveyard (1 = 15mins)\n')


def get_input():
    action = validate_and_transform(input('Give me: ').strip().split(' '))
    if action is None:
        print('Nope')
        exit(1)
    actions.append(action)


def validate_and_transform(input_list: List[str]) :
    if len(input_list) < 2 or len(input_list) > 3:
        return None

    try:
        int_list = [int(x) for x in input_list]
    except ValueError:
        return None

    if int_list[0] == 1:
        func = action1
    elif int_list[0] == 2:
        func = action2
    elif int_list[0] == 3:
        func = action3
    else:
        return None

    if len(int_list) == 2:
        return Action(func, None, int_list[1])
    else:
        return Action(func, int_list[1], int_list[2])


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
    print('actionn1111111')

def action2(driver: WebDriver):
    print('actionn2222')

def action3(driver: WebDriver):
    print('actionn333333')


if __name__ == '__main__':
    run()