import threading
import abc

from time import sleep
from enum import Enum
from os import path
from pathlib import Path
from typing import Callable, Any, List, Dict

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement


ACCOUNT_DETAILS_FILE_NAME = 'accountDetails.txt'
ASPECTS_FILE_NAME = 'aspects.txt'
EDGE_DRIVER_PATH = 'msedgedriver.exe'


class Account:
    def __init__(self, county: int, username: str, password: str):
        self.county = county
        self.username = username
        self.password = password
        self.page_url = self.__create_page_url()

    def __create_page_url(self) -> str:
        return 'https://s' + str(self.county) + '-en.bitefight.gameforge.com/profile'


class Action:
    def __init__(self, func: Callable[[], None], optional_sub_category: Any, amount: int):
        self.func = func
        self.optional_sub_category = optional_sub_category
        self.amount = amount

    def execute(self):
        self.func()


class Aspect(Enum):
    HUMAN = 1
    BEAST = 2
    KNOWLEDGE = 3
    DESTRUCTION = 4
    ORDER = 5
    CHAOS = 6
    NATURE = 7
    CORRUPTION = 8

    def opposite(self):
        if self == Aspect.BEAST:
            return Aspect.HUMAN
        elif self == Aspect.HUMAN:
            return Aspect.BEAST
        elif self == Aspect.CHAOS:
            return Aspect.ORDER
        elif self == Aspect.ORDER:
            return Aspect.CHAOS
        elif self == Aspect.CORRUPTION:
            return Aspect.NATURE
        elif self == Aspect.NATURE:
            return Aspect.CORRUPTION
        elif self == Aspect.DESTRUCTION:
            return Aspect.KNOWLEDGE
        elif self == Aspect.KNOWLEDGE:
            return Aspect.DESTRUCTION


class Implication(Enum):
    NONE = 0,
    BATTLE = 1,
    STRENGTH_CHECK = 2,
    DEXTERITY_CHECK = 3,
    ENDURANCE_CHECK = 4,
    CHARISMA_CHECK = 5

    def is_satisfied(self) -> bool:
        if self == Implication.NONE:
            return True
        elif self == Implication.BATTLE:
            return get_HP() > 4000
        else:
            return True


class Outcome(Enum):
    DAMAGE = -1,
    NONE = 0,
    BOOTY = 1,
    EXPERIENCE = 2,
    MONEY = 3,


class ActionSpecifications:
    def __init__(self, aspect: Aspect, amount: int, implication: Implication):
        self.aspect = aspect
        self.amount = amount
        self.implication = implication


class StoryAction(metaclass=abc.ABCMeta):
    def __init__(self, implication: Implication, outcomes: List[Outcome]):
        self.implication = implication
        self.outcomes = outcomes

    @abc.abstractmethod
    def calculate_value(self, aspect_value_dict: Dict[Aspect, int]) -> int:
        pass

    def calculate_outcomes_value(self) -> int:
        value = 0
        if Outcome.DAMAGE in self.outcomes:
            value -= 1
        if Outcome.EXPERIENCE in self.outcomes:
            value += 1
        if Outcome.BOOTY in self.outcomes:
            value += 1
        if Outcome.MONEY in self.outcomes:
            value += 1

        return value


class StatsAction(StoryAction):
    def __init__(self, aspect: Aspect, amount: int, implication: Implication, outcomes: List[Outcome]):
        super().__init__(implication, outcomes)
        self.aspect = aspect
        self.amount = amount

    def calculate_value(self, aspect_value_dict: Dict[Aspect, int]) -> int:
        return self.calculate_outcomes_value() + (aspect_value_dict[self.aspect] * self.amount)


class NeutralAction(StoryAction):
    def __init__(self, implication: Implication, outcomes: List[Outcome]):
        super().__init__(implication, outcomes)

    def calculate_value(self, aspect_value_dict: Dict[Aspect, int]) -> int:
        return self.calculate_outcomes_value()


def read_aspect_values_from_file() -> Dict[Aspect, int]:
    value_dict = dict()

    def fill_with(aspect: Aspect, _value: int):
        value_dict[aspect] = value
        value_dict[aspect.opposite()] = -value

    value = 25
    with open('files/'+ASPECTS_FILE_NAME, mode='r') as f:
        line = f.readline().strip()
        if line == Aspect.HUMAN.name:
            fill_with(Aspect.HUMAN, value)
        elif line == Aspect.BEAST.name:
            fill_with(Aspect.BEAST, value)
        elif line == Aspect.DESTRUCTION.name:
            fill_with(Aspect.DESTRUCTION, value)
        elif line == Aspect.KNOWLEDGE.name:
            fill_with(Aspect.KNOWLEDGE, value)
        elif line == Aspect.ORDER.name:
            fill_with(Aspect.ORDER, value)
        elif line == Aspect.CHAOS.name:
            fill_with(Aspect.CHAOS, value)
        elif line == Aspect.CORRUPTION.name:
            fill_with(Aspect.CORRUPTION, value)
        elif line == Aspect.NATURE.name:
            fill_with(Aspect.NATURE, value)
        value -= 5

    return value_dict


driver = webdriver.Edge(executable_path=EDGE_DRIVER_PATH)
actions: List[Action] = []
thread_exit_condition = False
# aspect_value_dict: Dict[Aspect, int] = read_values_from_file()
# actionRepository: Dict[str, StoryAction] = {
#         'aaa': StatsAction(Aspect.BEAST, 1, Implication.NONE, [Outcome.MONEY]),
#         'bbb': NeutralAction(Implication.BATTLE, [Outcome.MONEY, Outcome.MONEY]),
# }


def run():
    account = read_or_make_user_account()
    aspect_value_dict = read_or_rank_aspect_values()
    actionRepository = create_action_repository()

    tasks_thread = threading.Thread(target=execute_actions)
    tasks_thread.start()

    driver.get(account.page_url)
    login(account)

    while 1:
        show_actions()
        if not get_input():
            global thread_exit_condition
            thread_exit_condition = True
            break


def create_action_repository():
    return {
        'aaa': StatsAction(Aspect.BEAST, 1, Implication.NONE, [Outcome.MONEY]),
        'bbb': NeutralAction(Implication.BATTLE, [Outcome.MONEY, Outcome.MONEY]),
    }


def read_or_make_user_account():
    if path.exists('files/'+ACCOUNT_DETAILS_FILE_NAME):
        return read_account_from_file()
    else:
        return save_user_details()


def read_account_from_file():
    with open('files/'+ACCOUNT_DETAILS_FILE_NAME) as f:
        county = int(f.readline().strip())
        username = f.readline().strip()
        password = f.readline().strip()

    return Account(county, username, password)


def save_user_details():
    while 1:
        county = input('Give me the county(server) number: ').strip()
        if not county.isnumeric():
            print('County must be a number. Try again.')
            continue
        county = int(county)

        username = input('Give me the username: ').strip()
        if not username:
            print('Username cannot be empty.')
            continue

        password = input('Give me the password: ').strip()
        if not password:
            print('Password cannot be empty.')
            continue

        result = input('\nAre those details correct?\ncounty: {}\nusername: {}\npassword: {}\n(y/n):'
                       .format(county,username,password))
        if result == 'y':
            break
        else:
            print('Lets try again then\n')

    Path('files').mkdir(parents=True, exist_ok=True)
    with open('files/'+ACCOUNT_DETAILS_FILE_NAME, mode='w') as f:
        f.write(str(county))
        f.write('\n')
        f.write(username)
        f.write('\n')
        f.write(password)
        f.write('\n')

    return Account(county, username, password)


def rank_aspect_values():
    numeric = []
    while 1:
        user_input = input('\n{}) Human {}) Beast   {}) Knowledge {}) Destruction   {}) Order {}) Chaos   '
                                '{}) Nature {}) Corruption\n'
                           'Select the 4 aspects that you prefer, in preference order (spaces between like: 7 2 5 4): '
                           .format(Aspect.HUMAN.value, Aspect.BEAST.value,Aspect.KNOWLEDGE.value,Aspect.DESTRUCTION.value,
                                   Aspect.ORDER.value, Aspect.CHAOS.value,Aspect.NATURE.value,Aspect.CORRUPTION.value))

        array = [x.strip() for x in user_input.split(' ')]
        if len(array) != 4:
            print('You need to choose 4 of the 8 aspects.')
            continue

        try:
            numeric = [int(x) for x in array]
        except ValueError:
            print('The inputs must be numbers')
            continue

        if max(numeric) > 8 or min(numeric) < 1:
            print('Numbers must be between 1 and 8')
            continue

        if (1 in numeric and 2 in numeric) or (3 in numeric and 4 in numeric) or \
                (5 in numeric and 6 in numeric) or (7 in numeric and 8 in numeric):
            print('You cannot include 2 opposing aspects')
            continue

        break

    assert len(numeric) == 4

    with open('files/' + ASPECTS_FILE_NAME, mode='w') as f:
        for i in numeric:
            if i == Aspect.HUMAN.value:
                f.write(Aspect.HUMAN.name)
                f.write('\n')
            elif i == Aspect.BEAST.value:
                f.write(Aspect.BEAST.name)
                f.write('\n')
            elif i == Aspect.KNOWLEDGE.value:
                f.write(Aspect.KNOWLEDGE.name)
                f.write('\n')
            elif i == Aspect.DESTRUCTION.value:
                f.write(Aspect.DESTRUCTION.name)
                f.write('\n')
            elif i == Aspect.ORDER.value:
                f.write(Aspect.ORDER.name)
                f.write('\n')
            elif i == Aspect.CHAOS.value:
                f.write(Aspect.CHAOS.name)
                f.write('\n')
            elif i == Aspect.NATURE.value:
                f.write(Aspect.NATURE.name)
                f.write('\n')
            elif i == Aspect.CORRUPTION.value:
                f.write(Aspect.CORRUPTION.name)
                f.write('\n')


def read_or_rank_aspect_values() -> Dict[Aspect, int]:
    if not path.exists('files/' + ASPECTS_FILE_NAME):
        rank_aspect_values()

    return read_aspect_values_from_file()


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


def login(account: Account):
    print('Logging in...')
    try:
        username_field = driver.find_element_by_name('user')
    except Exception:
        return

    fill_input(username_field, account.username)
    fill_input(driver.find_element_by_name('pass'), account.password)

    try:
        driver.find_element_by_class_name('btn-small').click()
    except NoSuchElementException:
        driver.find_element_by_name('login').click()


def get_HP() -> int:
    return 23


def get_AP() -> int:
    return 10


def fill_input(_input: WebElement, text: str):
    _input.click()
    _input.send_keys(text)


def action1():
    print('actionn1111111')

def action2():
    print('actionn2222')

def action3():
    print('actionn333333')

def start_story(actionRepository, aspect_value_dict: Dict[Aspect, int]):
    btn_txt = ['dfd','dsd','ddd']
    max_value_action_index = -1
    max_value_action_value = 0
    for (i,txt) in btn_txt:
        storyAction = actionRepository[txt]
        if storyAction.implication.is_satisfied():
            value = storyAction.calculate_value(aspect_value_dict)
            if value > max_value_action_value:
                max_value_action_index = i




# def are_implications_satisfied(impl: Implication):



if __name__ == '__main__':
    run()
