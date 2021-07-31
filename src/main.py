import threading
import abc

from time import sleep
from os import path
from pathlib import Path
from enum import Enum
from typing import Callable, Any, List, Dict

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement


class Difficulty(Enum):
    EASY = 1,
    MEDIUM = 2,
    DIFFICULT = 3


class TimeUnit(Enum):
    SECONDS = 1,
    MINUTES = 60,
    HOURS   = 3600


class Outcome(Enum):
    DAMAGE = -1,
    NONE = 0,
    BOOTY = 1,
    EXPERIENCE = 2,
    MONEY = 3,


class ManHuntTarget(Enum):
    FARM = 1,
    VILLAGE = 2,
    SMALL_TOWN = 3,
    CITY = 4,
    METROPOLIS = 5


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



class Account:
    def __init__(self, county: int, username: str, password: str):
        self.county = county
        self.username = username
        self.password = password
        self.page_url = self.__create_page_url()

    def __create_page_url(self) -> str:
        return 'https://s' + str(self.county) + '-en.bitefight.gameforge.com/profile'



class FinishCondition(metaclass=abc.ABCMeta):
    def __init__(self, amount: int):
        self.amount = amount

    @abc.abstractmethod
    def is_satisfied(self, curr_amount: int) -> bool:
        pass


class AmountCondition(FinishCondition):
    def __init__(self, amount: int):
        super().__init__(amount)

    def is_satisfied(self, curr_amount: int) -> bool:
        return curr_amount >= self.amount


class HealthGuard(FinishCondition):
    def __init__(self, amount: int):
        super().__init__(amount)

    def is_satisfied(self, curr_amount: int) -> bool:
        return curr_amount <= self.amount


class TimeLimit(FinishCondition):
    def __init__(self, amount: int, unit: TimeUnit):
        super().__init__(amount)
        self.unit = unit

    def is_satisfied(self, curr_amount: int) -> bool:
        pass



class Action(metaclass=abc.ABCMeta):
    def __init__(self, finish_condition: FinishCondition):
        self.finish_condition = finish_condition

    @abc.abstractmethod
    def execute(self):
        pass


class ManHuntAction(Action):
    def __init__(self, target: ManHuntTarget, finish_condition: FinishCondition):
        super().__init__(finish_condition)
        self.target = target

    def execute(self):
        pass


class GrottoAction(Action):
    def __init__(self, difficulty: Difficulty, finish_condition: FinishCondition):
        super().__init__(finish_condition)
        self.difficulty = difficulty

    def execute(self):
        pass


class GraveyardAction(Action):
    def execute(self):
        pass

class TavernAction(Action):
    def execute(self):
        pass



class StoryChoice(metaclass=abc.ABCMeta):
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


class StatsChoice(StoryChoice):
    def __init__(self, aspect: Aspect, amount: int, implication: Implication, outcomes: List[Outcome]):
        super().__init__(implication, outcomes)
        self.aspect = aspect
        self.amount = amount

    def calculate_value(self, aspect_value_dict: Dict[Aspect, int]) -> int:
        return self.calculate_outcomes_value() + (aspect_value_dict[self.aspect] * self.amount)


class NeutralChoice(StoryChoice):
    def __init__(self, implication: Implication, outcomes: List[Outcome]):
        super().__init__(implication, outcomes)

    def calculate_value(self, aspect_value_dict: Dict[Aspect, int]) -> int:
        return self.calculate_outcomes_value()



ACCOUNT_DETAILS_FILE_NAME = 'accountDetails.txt'
ASPECTS_FILE_NAME = 'aspects.txt'
EDGE_DRIVER = 'msedgedriver.exe'
driver = webdriver.Edge(executable_path=EDGE_DRIVER)
actions: List[Action] = []
thread_exit_condition = False


def run():
    print('Initializing...')
    account = read_or_make_user_account()
    aspect_value_dict = read_or_rank_aspect_values()
    actionRepository = create_action_repository()

    print('Logging in...')
    driver.get(account.page_url)
    if login(account):
        print('Success\n')
    else:
        print('Unable to log in. Terminating.')
        exit(1)

    tasks_thread = threading.Thread(target=execute_actions)
    tasks_thread.start()

    while 1:
        if not get_new_action():
            global thread_exit_condition
            thread_exit_condition = True
            break


def login(account: Account) -> bool:
    try:
        username_field = driver.find_element_by_name('user')
    except Exception:
        return False

    fill_input(username_field, account.username)
    fill_input(driver.find_element_by_name('pass'), account.password)

    try:
        driver.find_element_by_class_name('btn-small').click()
    except NoSuchElementException:
        try:
            driver.find_element_by_name('login').click()
        except NoSuchElementException:
            return False

    try:
        driver.find_element_by_class_name('error')
        return False
    except NoSuchElementException:
        return True


def start_story(actionRepository: Dict[str, StoryChoice], aspect_value_dict: Dict[Aspect, int]):
    btn_txt = ['dfd','dsd','ddd']
    max_value_action_index = -1
    max_value_action_value = 0
    for (i,txt) in btn_txt:
        storyAction = actionRepository[txt]
        if storyAction.implication.is_satisfied():
            value = storyAction.calculate_value(aspect_value_dict)
            if value > max_value_action_value:
                max_value_action_index = i


def create_action_repository() -> Dict[str, StoryChoice]:
    return {
        'aaa': StatsChoice(Aspect.BEAST, 1, Implication.NONE, [Outcome.MONEY]),
        'bbb': NeutralChoice(Implication.BATTLE, [Outcome.MONEY, Outcome.MONEY]),
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


def get_new_action() -> bool:
    while 1:
        print('1) ManHunt   2) Grotto   3) Story   4) Graveyard   5) Idle   0) Exit')
        user_in = input('choose an action: ')

        if user_in.isnumeric():
            user_in = int(user_in)
        else:
            print('Input must be a number.\n')
            continue

        if 0 > user_in > 5:
            print('Input must be between 0 and 5.\n')
            continue

        if user_in == 0:
            return False
        elif user_in == 1:
            manhunt = take_manhunt_input()
            if manhunt is None:
                continue
            else:
                actions.append(manhunt)
        elif user_in == 2:
            grotto = take_grotto_input()
            if grotto is None:
                continue
            else:
                actions.append(grotto)
        elif user_in == 3:
            story = take_story_input()
            if story is None:
                continue
            else:
                actions.append(story)
        elif user_in == 4:
            graveyard = take_graveyard_input()
            if graveyard is None:
                continue
            else:
                actions.append(graveyard)
        elif user_in == 5:
            idle = take_idle_input()
            if idle is None:
                continue
            else:
                actions.append(idle)

        return True


def take_manhunt_input():
    pass


def take_grotto_input():
    pass


def take_story_input():
    pass


def take_graveyard_input():
    pass


def take_idle_input():
    #every action will have its own finish conditions!
    pass


def get_HP() -> int:
    return 23


def get_AP() -> int:
    return 10


def fill_input(_input: WebElement, text: str):
    _input.click()
    _input.send_keys(text)



if __name__ == '__main__':
    run()
