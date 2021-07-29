import threading
from time import sleep
from enum import Enum

from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from typing import Callable, Any, List, Dict

USERNAME = 'petros21'
PASSWORD = 'Smallville21'
EDGE_DRIVER_PATH = 'msedgedriver.exe'
PAGE_URL = 'https://s37-en.bitefight.gameforge.com/profile'


class Action:
    def __init__(self, func: Callable[[], None], optional_sub_category: Any, amount: int):
        self.func = func
        self.optional_sub_category = optional_sub_category
        self.amount = amount

    def execute(self):
        self.func()


class AspectID(Enum):
    HUMAN = 'Human'
    KNOWLEDGE = 'Knowledge'
    ORDER = 'Order'
    NATURE = 'Nature'
    BEAST = 'Beast'
    DESTRUCTION = 'Destruction'
    CHAOS = 'Chaos'
    CORRUPTION = 'Corruption'


class StoryActionRepository:
    def __init__(self):
        self.actions: Dict[str, (AspectID, int)] = {
            'fdffdf': (AspectID.BEAST,1)
        }


driver = webdriver.Edge(executable_path=EDGE_DRIVER_PATH)
actions: List[Action] = []
thread_exit_condition = False
aspect_value_dict: Dict[AspectID, int] = dict()
actionRepository = StoryActionRepository()


def run():
    tasks_thread = threading.Thread(target=execute_actions)
    tasks_thread.start()

    while 1:
        show_actions()
        if not get_input():
            global thread_exit_condition
            thread_exit_condition = True
            break

    # actions[0].execute()
    # driver.get(PAGE_URL)
    # login()


def save_user_details():
    while 1:
        username = input('Give me the username: ')
        password = input('Give me the password: ')
        result = input('Are those details correct?\nusername: {}\npassword:{}\n\n(y/n):'.format(username,password))
        if result == 'y':
            break
        else:
            print('Lets try again then\n')



def execute_actions():
    global thread_exit_condition
    while not thread_exit_condition:
        if actions:
            actions.pop().execute()
        else:
            sleep(1)
    print("thread yok")


def show_actions():
    print('format: <action_num> <optional_sub_category_num> <amount_num>')
    print('1. Hunt\n'
          '       1. ManHunt 2. Village 3. Small Town 4. City\n'
          '2. Story (1 = 40 story actions)\n'
          '3. Graveyard (1 = 15mins)\n')


def get_input() -> bool:
    user_input = input('Give me: ').strip()
    if user_input == '0':
        print("ya")
        return False

    action = validate_and_transform(user_input.split(' '))
    if action is not None:
        actions.append(action)

    return True


def validate_and_transform(input_list: List[str]):
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


def login():
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


def action1():
    print('actionn1111111')

def action2():
    print('actionn2222')

def action3():
    print('actionn333333')

def start_story():
    btn_txt = ['dfd','dsd','ddd']
    max_value_action_index = 0
    max_value_action_value = 0
    for (i,txt) in btn_txt:
        (aspect,num) = actionRepository.actions[txt]
        value = aspect_value_dict[aspect] * num
        if value > max_value_action_value:
            max_value_action_index = i



if __name__ == '__main__':
    run()
