import threading
import abc

from os import path
from pathlib import Path
from enum import Enum, IntEnum
from queue import Queue
from time import sleep
from typing import List, Dict, Optional
from threading import Event

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, NoSuchWindowException, WebDriverException
from selenium.webdriver.remote.webelement import WebElement


class Difficulty(IntEnum):
    EASY = 1,
    MEDIUM = 2,
    DIFFICULT = 3


class Outcome(Enum):
    DAMAGE = -1,
    NONE = 0,
    BOOTY = 1,
    EXPERIENCE = 2,
    MONEY = 3,
    DISCOVERY = 4


class ManHuntTarget(IntEnum):
    FARM = 1
    VILLAGE = 2
    SMALL_TOWN = 3
    CITY = 4
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



class Result(metaclass=abc.ABCMeta):
    def __init__(self, value=None):
        self.value = value

    @abc.abstractmethod
    def is_ok(self) -> bool:
        pass

    @abc.abstractmethod
    def is_err(self) -> bool:
        pass


class Ok(Result):
    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False


class Err(Result):
    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True



class Account:
    def __init__(self, county: int, username: str, password: str):
        self.county = county
        self.username = username
        self.password = password
        self.page_url = self.__create_page_url()

    def __create_page_url(self) -> str:
        return 'https://s' + str(self.county) + '-en.bitefight.gameforge.com/profile'



def check_for_window(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (NoSuchWindowException, WebDriverException):
            return Err('Browser window was manually tampered with. Terminating.')
        except Exception as e:
            if debug_mode:
                raise e
            else:
                return Err('Terminating due to unexpected error.')
    return inner


def check_for_mission_window():
    try:
        driver.find_element_by_class_name('buttonOverlay')
        driver.find_elements_by_class_name('btn')[1].click()
    except NoSuchElementException:
        pass


class Action(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def execute(self) -> Result:
        pass

    @abc.abstractmethod
    def __str__(self):
        pass


class ManHuntAction(Action):
    def __init__(self, target: ManHuntTarget, amount: int):
        self.target = target
        self.amount = amount

    @check_for_window
    def execute(self) -> Result:
        driver.find_element_by_link_text('Hunt').click()
        driver.find_elements_by_class_name('mjs')[int(self.target)-1].click()

        iterations = min(int(get_AP()/get_manhunt_target_cost(self.target)), self.amount)
        counter = 1
        while counter < iterations:
            try:
                while counter < iterations:
                    driver.find_element_by_xpath('//button[text()="Again "]').click()
                    check_for_mission_window()
                    counter += 1
            except NoSuchElementException:
                driver.find_element_by_xpath('//a[text()="back"]').find_element_by_xpath('..').click()
                driver.find_elements_by_class_name('mjs')[int(self.target) - 1].click()
                check_for_mission_window()
                counter += 1

        if iterations != self.amount:
            return Ok('Grotto action stopped after {} iterations due to low AP'.format(counter))
        else:
            return Ok('ManHunt action finished successfully.')

    def __str__(self):
        return '{}({})'.format(self.target.name,self.amount)


def get_manhunt_target_cost(target: ManHuntTarget):
    if target == ManHuntTarget.FARM or target == ManHuntTarget.VILLAGE:
        return 1
    if target == ManHuntTarget.SMALL_TOWN or ManHuntTarget.CITY:
        return 2
    if target == ManHuntTarget.METROPOLIS:
        return 3


class GrottoAction(Action):
    def __init__(self, difficulty: Difficulty, amount: int):
        self.difficulty = difficulty
        self.amount = amount

    @check_for_window
    def execute(self) -> Result:
        driver.find_element_by_link_text('City').click()
        driver.find_element_by_link_text('Grotto').click()

        iterations = min(get_AP(),self.amount)
        hp_guard = 2000 + 1000*int(self.difficulty)
        counter = 0
        while counter < iterations and get_HP() > hp_guard:
            driver.find_elements_by_name('difficulty')[int(self.difficulty)-1].click()
            check_for_mission_window()
            driver.find_element_by_xpath('//a[text()="back"]').find_element_by_xpath('..').click()
            counter += 1

        if iterations != self.amount:
            return Ok('Grotto action stopped after {} iterations due to low AP'.format(counter))
        elif counter != self.amount:
            return Ok('Grotto action stopped after {} iterations due to low HP'.format(counter))
        else:
            return Ok('Grotto action finished successfully.')

    def __str__(self):
        return 'Grotto({}, {})'.format(self.difficulty.name,self.amount)


class GraveyardAction(Action):
    def __init__(self, amount: int):
        self.amount = amount

    @check_for_window
    def execute(self) -> Result:
        driver.find_element_by_link_text('City').click()
        driver.find_element_by_link_text('Graveyard').click()
        for i in range(0,self.amount):
            driver.find_element_by_name('dowork').click()
            sleep((60 * 15) + 5)

        return Ok('Graveyard action finished successfully.')

    def __str__(self):
        return 'Graveyard({})'.format(self.amount)


class TavernAction(Action):
    def __init__(self, amount: int):
        self.amount = amount

    @check_for_window
    def execute(self) -> Result:
        if get_AP() < 3:
            return Ok('Tavern Story action not performed due to low AP')

        driver.find_element_by_link_text('City').click()
        driver.find_element_by_link_text('Tavern').click()
        driver.find_elements_by_class_name('buttonOverlay')[0].click()
        driver.find_element_by_class_name('btn-right').click()

        global actionRepository
        for i in range(0,40):
            choices = [txt for btn in driver.find_elements_by_class_name('btn_right')
                           for txt in btn.find_element_by_xpath('.//*').text]

            best_choice = max(choices, key=lambda a: actionRepository[a].calculate_value())
            driver.find_element_by_link_text(best_choice).click()


    def __str__(self):
        return 'Tavern({})'.format(self.amount)


class HealAction(Action):
    @check_for_window
    def execute(self):
        driver.find_element_by_link_text('City').click()
        driver.find_element_by_link_text('Church').click()

        try:
            driver.find_element_by_name('heal').find_element_by_xpath('..').click()
            return Ok('Heal action performed successfully')
        except NoSuchElementException:
            return Ok('Heal action failed due to insufficient AP')

    def __str__(self):
        return 'Heal'


class StoryChoice(metaclass=abc.ABCMeta):
    def __init__(self, implication: Implication, outcomes: List[Outcome]):
        self.implication = implication
        self.outcomes = outcomes

    @abc.abstractmethod
    def calculate_value(self) -> int:
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

    def calculate_value(self) -> int:
        return self.calculate_outcomes_value() + (aspect_value_dict[self.aspect] * self.amount)


class NeutralChoice(StoryChoice):
    def __init__(self, implication: Implication, outcomes: List[Outcome]):
        super().__init__(implication, outcomes)

    def calculate_value(self) -> int:
        return self.calculate_outcomes_value()



ACCOUNT_DETAILS_FILE_NAME = 'accountDetails.txt'
ASPECTS_FILE_NAME = 'aspects.txt'
EDGE_DRIVER = 'msedgedriver.exe'
driver = webdriver.Edge(executable_path=EDGE_DRIVER)

debug_mode: bool = True

actions: Queue[Action] = Queue()
aspect_value_dict = dict()
actionRepository = dict()


def run():
    global aspect_value_dict, actionRepository

    print('Initializing...')
    account = read_or_make_user_account()
    aspect_value_dict = read_or_rank_aspect_values()
    actionRepository = create_action_repository()

    print('Logging in...')
    driver.get(account.page_url)
    login_result = login(account)
    if login_result.is_ok():
        print('Success\n')
    else:
        print(login_result.value)
        print('Terminating.')
        return

    accept_cookies()

    exit_event = Event()
    tasks_thread = threading.Thread(target=get_inputs, args=(exit_event,), daemon=True)
    tasks_thread.start()

    execute_actions(exit_event)


def get_inputs(exit_event: Event):
    while not exit_event.is_set():
        if not actions.empty():
            print('Queued actions: ', ', '.join([str(a) for a in actions.queue]))
        if get_new_action():
            print('Action queued!\n')
        else:
            exit_event.set()
            break


def execute_actions(exit_event: Event):
    while not exit_event.is_set():
        if actions:
            exec_result = actions.get().execute()
            print('\n',exec_result.value)
            if exec_result.is_err():
                exit_event.set()
        else:
            sleep(1)


def login(account: Account) -> Result:
    try:
        username_field = driver.find_element_by_name('user')
    except Exception:
        return Err('Login failed. Username field could not be found.')

    fill_input(username_field, account.username)
    fill_input(driver.find_element_by_name('pass'), account.password)

    try:
        driver.find_element_by_class_name('btn-small').click()
    except NoSuchElementException:
        try:
            driver.find_element_by_name('login').click()
        except NoSuchElementException:
            return Err('Login failed. Login button could not be found.')

    try:
        driver.find_element_by_id('loginName2')
        return Err('Login failed. Credentials are incorrect.')
    except NoSuchElementException:
        return Ok()


def accept_cookies():
    driver.find_elements_by_class_name('cookiebanner5')[1].click()


def start_story():
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
        # 'Examine'                  : NeutralChoice(Implication.BATTLE, [Outcome.MONEY, Outcome.MONEY]),
        'Examine'                  : StatsChoice(Aspect.KNOWLEDGE, 1, Implication.NONE, []),
        'Investigate'                  : StatsChoice(Aspect.KNOWLEDGE, 2, Implication.NONE, []),
        'Observe'                  : StatsChoice(Aspect.KNOWLEDGE, 2, Implication.NONE, []),
        'Enter City'                  : StatsChoice(Aspect.HUMAN, 1, Implication.NONE, []),
        'Rob City'                  : StatsChoice(Aspect.BEAST, 2, Implication.NONE, []),
        'Rob'                  : StatsChoice(Aspect.BEAST, 1, Implication.NONE, []),
        'Terrorise'                  : StatsChoice(Aspect.CHAOS, 1, Implication.NONE, []),
        'Brave'                  : StatsChoice(Aspect.ORDER, 2, Implication.NONE, []),
        'Accept'                  : StatsChoice(Aspect.NATURE, 1, Implication.NONE, []),
        'Use chance'                  : StatsChoice(Aspect.KNOWLEDGE, 1, Implication.NONE, []),
        'Ask for more'                  : StatsChoice(Aspect.CORRUPTION, 1, Implication.NONE, []),
        'Hide'                  : StatsChoice(Aspect.NATURE, 1, Implication.NONE, []),
        'Assassinate'                  : StatsChoice(Aspect.CORRUPTION, 1, Implication.NONE, []),
        'Full attack'                  : StatsChoice(Aspect.BEAST, 1, Implication.NONE, []),
        'Confront the enemy'                  : StatsChoice(Aspect.ORDER, 2, Implication.NONE, []),
        'Set everything alight'                  : StatsChoice(Aspect.CHAOS, 2, Implication.NONE, []),
        'Escort'                  : StatsChoice(Aspect.ORDER, 2, Implication.NONE, []),
        'Beguile'                  : StatsChoice(Aspect.HUMAN, 1, Implication.NONE, []),
        'Warn of dangers'                  : StatsChoice(Aspect.HUMAN, 2, Implication.NONE, []),
        'Snoop'                  : StatsChoice(Aspect.BEAST, 1, Implication.NONE, []),
        'Smash everything'                  : StatsChoice(Aspect.DESTRUCTION, 1, Implication.NONE, []),
        'Throw a coin in'                  : StatsChoice(Aspect.KNOWLEDGE, 1, Implication.NONE, []),
        'Look for coins'                  : StatsChoice(Aspect.CORRUPTION, 2, Implication.NONE, []),
        'Party'                  : StatsChoice(Aspect.HUMAN, 2, Implication.NONE, []),
        'Make some valuable booty' : NeutralChoice(Implication.NONE, [Outcome.MONEY, Outcome.BOOTY, Outcome.EXPERIENCE]),
        'Look for a better path'                  : StatsChoice(Aspect.HUMAN, 1, Implication.NONE, []),
        'Jump over it'                  : StatsChoice(Aspect.BEAST, 2, Implication.NONE, []),
        'Mislead'                  : StatsChoice(Aspect.CORRUPTION, 1, Implication.NONE, []),
        'Devour'                  : StatsChoice(Aspect.BEAST, 1, Implication.NONE, []),
        'Talk'                  : StatsChoice(Aspect.KNOWLEDGE, 1, Implication.NONE, []),
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




def get_new_action() -> bool:
    while 1:
        print('1) ManHunt   2) Grotto   3) Story   4) Graveyard   5) Heal   0) Exit')
        user_in = input('choose an action: ')

        if user_in.isnumeric():
            user_in = int(user_in)
        else:
            print('Input must be a number.\n')
            continue

        if user_in < 0 or user_in > 5:
            print('Input must be between 0 and 5.\n')
            continue

        if user_in == 0:
            return False
        elif user_in == 1:
            manhunt = take_manhunt_input()
            if manhunt is None:
                continue
            else:
                actions.put(manhunt)
        elif user_in == 2:
            grotto = take_grotto_input()
            if grotto is None:
                continue
            else:
                actions.put(grotto)
        elif user_in == 3:
            actions.put(take_tavern_input())
        elif user_in == 4:
            actions.put(take_graveyard_input())
        elif user_in == 5:
            actions.put(HealAction())

        return True


def take_manhunt_input():
    while 1:
        msg = '  1) Farm   2) Village   3) Small Town   4) City   5) Metropolis   0) Cancel\n' \
                      '  Choose category: '

        result = get_int_inputs(msg, 5)
        if result is None:
            print('  Invalid input\n')
            continue

        return ManHuntAction(ManHuntTarget(result[0]), result[1])


def take_grotto_input():
    while 1:
        msg = '  1) {}   2) {}   3) {}   0) Cancel\n' \
                           '  Choose difficulty: '.format(Difficulty.EASY.name, Difficulty.MEDIUM.name,
                                                          Difficulty.DIFFICULT.name)
        result = get_int_inputs(msg, 3)
        if result is None:
            print('  Invalid input\n')
            continue

        return GrottoAction(Difficulty(result[0]), result[1])


def take_tavern_input():
    while 1:
        amount = input('How many? ').strip()

        if not amount.isnumeric():
            print('Invalid input')
            continue

        return TavernAction(int(amount))


def take_graveyard_input():
    while 1:
        amount = input('How many? ').strip()

        if not amount.isnumeric():
            print('Invalid input')
            continue

        return GraveyardAction(int(amount))


def get_int_inputs(msg: str, _max: int):
    a = input(msg)
    if not a.isnumeric():
        return None

    a = int(a)
    if a < 0 or a > _max:
        return None

    amount = input('  How many? ').strip()
    if not amount.isnumeric():
        return None
    amount = int(amount)

    return a, amount


def get_HP() -> int:
    upper_bar_text = get_text_excluding_children(driver.find_element_by_class_name('gold'))
    hp_text:str = upper_bar_text.strip().split('\n')[4].strip()
    hp = hp_text[0 : hp_text.find('/')]
    hp = hp.replace('.','')

    return int(hp)


def get_AP() -> int:
    upper_bar_text = get_text_excluding_children(driver.find_element_by_class_name('gold'))
    ap_text: str = upper_bar_text.strip().split('\n')[3].strip()
    ap = ap_text[0: ap_text.find('/')]

    return int(ap)

def get_text_excluding_children(element):
    return driver.execute_script("""
    return jQuery(arguments[0]).contents().filter(function() {
        return this.nodeType == Node.TEXT_NODE;
    }).text();
    """, element)


def fill_input(_input: WebElement, text: str):
    _input.click()
    _input.send_keys(text)



if __name__ == '__main__':
    run()
