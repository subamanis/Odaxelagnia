import os
import threading
import abc

from os import path
from pathlib import Path
from enum import Enum, IntEnum
from queue import Queue
from time import sleep
from typing import List, Dict
from threading import Event

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, NoSuchWindowException, WebDriverException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


class Browser(Enum):
    CHROME  = 'CHROME'
    EDGE    = 'EDGE'
    FIREFOX = 'FIREFOX'


class Difficulty(IntEnum):
    EASY = 1
    MEDIUM = 2
    DIFFICULT = 3


class Outcome(IntEnum):
    DAMAGE = -1
    NONE = 0
    BOOTY = 1
    EXPERIENCE = 1
    MONEY = 1
    ITEM_DISCOVERY = 1
    FAKE_POSITIVE = 1
    HEALING = 1


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
        except (NoSuchWindowException, WebDriverException) as e:
            if debug_mode:
                raise e
            else:
                driver.quit()
                return Err('Browser window entered an invalid state. Terminating.')
        except Exception as e:
            if debug_mode:
                raise e
            else:
                driver.quit()
                return Err('Terminating due to unexpected error.')
    return inner


def check_for_mission_window():
    try:
        click(driver.find_elements_by_class_name('buttonOverlay')[1])
    except Exception:
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
        click(driver.find_elements_by_class_name('mjs')[int(self.target)-1])

        iterations = min(int(get_AP()/get_manhunt_target_cost(self.target)), self.amount)
        counter = 1
        while counter < iterations:
            try:
                while counter < iterations:
                    click(driver.find_element_by_xpath('//button[text()="Again "]'))
                    check_for_mission_window()
                    counter += 1
            except NoSuchElementException:
                click(driver.find_element_by_xpath('//a[text()="back"]').find_element_by_xpath('..'))
                click(driver.find_elements_by_class_name('mjs')[int(self.target) - 1])
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
        click(driver.find_element_by_link_text('Grotto'))

        iterations = min(get_AP(),self.amount)
        hp_guard = 2000 + 1000*int(self.difficulty)
        counter = 0
        while counter < iterations and get_HP() > hp_guard:
            click(driver.find_elements_by_name('difficulty')[int(self.difficulty)-1])
            check_for_mission_window()
            click(driver.find_element_by_xpath('//a[text()="back"]').find_element_by_xpath('..'))
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
        click(driver.find_element_by_link_text('Graveyard'))
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
        click(driver.find_element_by_link_text('Tavern'))
        click(driver.find_elements_by_class_name('buttonOverlay')[0])
        click(driver.find_element_by_class_name('btn-right'))

        global actionRepository
        story_count = 0
        while 1:
            story_count += 1
            counter = 1
            while counter < 40:
                choices = [btn.text.strip() for btn in driver.find_elements_by_class_name('btn')[1:]]
                if not choices:
                    if get_HP() < 1000:
                        return Ok('Tavern Story action finished due to low HP after {} choices'
                                  .format(calculate_choices_num(story_count,counter)))
                    else:
                        return Ok('Tavern Story action finished unexpectedly after {} choices'
                                  .format(calculate_choices_num(story_count,counter)))
                elif len(choices) == 1:
                    click(driver.find_element_by_link_text(choices[0]))
                    continue

                if debug_mode:
                    print('choices: ',choices)

                best_choice = max(choices, key=lambda a: calculate_tavern_choice_value(a))
                if debug_mode:
                    print('best: ',best_choice)
                click(driver.find_element_by_link_text(best_choice))
                counter += 1

            if len(driver.find_elements_by_class_name('btn')) == 2:
                click(driver.find_elements_by_class_name('btn')[1])

            if story_count < self.amount and get_AP() >= 3:
                click(driver.find_elements_by_class_name('btn')[1])
            else:
                click(driver.find_elements_by_class_name('btn')[2])
                break


        if self.amount == story_count:
            return Ok('Tavern Story action finished successfully.')
        else:
            return Ok('Tavern Story finished after {} iterations due to low AP'.format(story_count))

    def __str__(self):
        return 'Tavern({})'.format(self.amount)


def calculate_choices_num(story_count: int, counter:int) -> int:
    return (story_count - 1) * 40 + counter


def calculate_tavern_choice_value(name: str) -> int:
    try:
        return actionRepository[name].calculate_value()
    except KeyError:
        return -100


class HealAction(Action):
    @check_for_window
    def execute(self):
        driver.find_element_by_link_text('City').click()
        click(driver.find_element_by_link_text('Church'))

        try:
            click(driver.find_element_by_name('heal').find_element_by_xpath('..'))
            return Ok('Heal action performed successfully')
        except NoSuchElementException:
            return Ok('Heal action failed due to insufficient AP')

    def __str__(self):
        return 'Heal'



class AspectChange:
    def __init__(self, aspect: Aspect, amount: int):
        self.aspect = aspect
        self.amount = amount
        global aspect_value_dict
        self.value = aspect_value_dict[aspect] * amount


class StoryChoice(metaclass=abc.ABCMeta):
    def __init__(self, implication: Implication, outcomes: List[Outcome]):
        self.implication = implication
        self.outcomes = outcomes

    @abc.abstractmethod
    def calculate_value(self) -> int:
        pass

    def calculate_outcomes_value(self) -> int:
        value = 0
        for outcome in self.outcomes:
            value += int(outcome)

        return value


class StatsChoice(StoryChoice):
    def __init__(self, aspect_changes: List[AspectChange], implication: Implication, outcomes: List[Outcome]):
        super().__init__(implication, outcomes)
        self.aspect_changes = aspect_changes

    def calculate_value(self) -> int:
        return self.calculate_outcomes_value() + (sum(change.value for change in self.aspect_changes))


class NeutralChoice(StoryChoice):
    def __init__(self, implication: Implication, outcomes: List[Outcome]):
        super().__init__(implication, outcomes)

    def calculate_value(self) -> int:
        return self.calculate_outcomes_value()


def read_or_save_browser_preference():
    if path.exists('files/'+BROWSER_CHOICE_FILE_NAME):
        return read_browser_file()
    else:
        return save_browser_preference()



ACCOUNT_DETAILS_FILE_NAME = 'accountDetails.txt'
ASPECTS_FILE_NAME = 'aspects.txt'
BROWSER_CHOICE_FILE_NAME = 'browser.txt'
EDGE_DRIVER = 'msedgedriver.exe'
CHROME_DRIVER = 'chromedriver.exe'
FIREFOX_DRIVER = 'geckodriver.exe'
CLICK_DELAY = 0.12
driver: WebDriver

debug_mode: bool = False

actions: Queue[Action] = Queue()
aspect_value_dict = dict()
actionRepository = dict()


def run():
    global aspect_value_dict, actionRepository, driver

    print('Initializing...')
    account = read_or_make_user_account()
    aspect_value_dict = read_or_rank_aspect_values()
    actionRepository = create_action_repository()
    driver = read_or_save_browser_preference()

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

@check_for_window
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
    try:
        driver.find_elements_by_class_name('cookiebanner5')[1].click()
    except Exception:
        pass


def create_action_repository() -> Dict[str, StoryChoice]:
    return {
        'Examine'                    : StatsChoice([AspectChange(Aspect.KNOWLEDGE, 1)], Implication.NONE, []),
        'Investigate'                : StatsChoice([AspectChange(Aspect.KNOWLEDGE, 2)], Implication.NONE, []),
        'Observe'                    : StatsChoice([AspectChange(Aspect.KNOWLEDGE, 2)], Implication.NONE, []),
        'Enter City'                 : StatsChoice([AspectChange(Aspect.HUMAN, 1)], Implication.NONE, []),
        'Rob city'                   : StatsChoice([AspectChange(Aspect.BEAST, 2)], Implication.NONE, [Outcome.EXPERIENCE]),
        'Rob'                        : StatsChoice([AspectChange(Aspect.BEAST, 1)], Implication.NONE, [Outcome.MONEY]),
        'Terrorise'                  : StatsChoice([AspectChange(Aspect.CHAOS, 1)], Implication.NONE, []),
        'Brave'                      : StatsChoice([AspectChange(Aspect.ORDER, 2)], Implication.NONE, [Outcome.MONEY]),
        'Accept'                     : StatsChoice([AspectChange(Aspect.NATURE, 1)], Implication.NONE, [Outcome.DAMAGE]),
        'Use chance'                 : StatsChoice([AspectChange(Aspect.KNOWLEDGE, 1)], Implication.NONE, []),
        'Ask for more'               : StatsChoice([AspectChange(Aspect.CORRUPTION, 1)], Implication.NONE, []),
        'Hide'                       : StatsChoice([AspectChange(Aspect.NATURE, 1)], Implication.NONE, []),
        'Assassinate'                : StatsChoice([AspectChange(Aspect.CORRUPTION, 1)], Implication.NONE, []),
        'Full attack'                : StatsChoice([AspectChange(Aspect.BEAST, 1), AspectChange(Aspect.DESTRUCTION,1)],
                                                   Implication.BATTLE, [Outcome.EXPERIENCE, Outcome.MONEY, Outcome.DAMAGE]),
        'Confront the enemy'         : StatsChoice([AspectChange(Aspect.ORDER, 2)], Implication.BATTLE,
                                                   [Outcome.MONEY, Outcome.EXPERIENCE, Outcome.DAMAGE]),
        'Set everything alight'      : StatsChoice([AspectChange(Aspect.CHAOS, 2)], Implication.NONE, []),
        'Escort'                     : StatsChoice([AspectChange(Aspect.ORDER, 2)], Implication.NONE, []),
        'Beguile'                    : StatsChoice([AspectChange(Aspect.HUMAN, 1), AspectChange(Aspect.CORRUPTION,1)],
                                                   Implication.NONE, []),
        'Warn of dangers'            : StatsChoice([AspectChange(Aspect.HUMAN, 2)], Implication.NONE, []),
        'Snoop'                      : StatsChoice([AspectChange(Aspect.BEAST, 1)], Implication.NONE, []),
        'Smash everything'           : StatsChoice([AspectChange(Aspect.DESTRUCTION, 1)], Implication.NONE, []),
        'Throw a coin in'            : StatsChoice([AspectChange(Aspect.KNOWLEDGE, 1)], Implication.NONE, []),
        'Look for coins'             : StatsChoice([AspectChange(Aspect.CORRUPTION, 2)], Implication.NONE, []),
        'Party'                      : StatsChoice([AspectChange(Aspect.HUMAN, 2)], Implication.NONE, []),
        'Look for a better path'     : StatsChoice([AspectChange(Aspect.HUMAN, 1)], Implication.NONE, []),
        'Jump over it'               : StatsChoice([AspectChange(Aspect.BEAST, 2)], Implication.NONE, []),
        'Mislead'                    : StatsChoice([AspectChange(Aspect.CORRUPTION, 1)], Implication.NONE, []),
        'Devour'                     : StatsChoice([AspectChange(Aspect.BEAST, 1)], Implication.NONE, []),
        'Talk'                       : StatsChoice([AspectChange(Aspect.KNOWLEDGE, 1)], Implication.NONE, []),
        'Make some valuable booty'   : NeutralChoice(Implication.NONE, [Outcome.MONEY, Outcome.BOOTY, Outcome.EXPERIENCE]),
        'Carry on walking'           : NeutralChoice(Implication.NONE, []),
        'Shadow bones'               : NeutralChoice(Implication.DEXTERITY_CHECK, [Outcome.EXPERIENCE]),
        'Death aura'                 : NeutralChoice(Implication.CHARISMA_CHECK, [Outcome.MONEY]),
        'Vampire`s gaze'             : NeutralChoice(Implication.CHARISMA_CHECK, [Outcome.DAMAGE]),
        'Find fortune in misfortune' : NeutralChoice(Implication.NONE, []),
        'Enter forest'               : NeutralChoice(Implication.NONE, []),
        'Enter the cavern'           : NeutralChoice(Implication.NONE, []),
        'Tread the mountain path'    : NeutralChoice(Implication.NONE, []),
        'Step into the depths'       : NeutralChoice(Implication.NONE, []),
        'Stay here'                  : NeutralChoice(Implication.NONE, [Outcome.FAKE_POSITIVE]),
    }


def read_or_make_user_account():
    if path.exists('files/'+ACCOUNT_DETAILS_FILE_NAME):
        try:
            return read_account_from_file()
        except Exception:
            print('Account details file has invalid data. Lets overwrite it')
            return save_user_details()
    else:
        return save_user_details()


def read_account_from_file():
    with open('files/'+ACCOUNT_DETAILS_FILE_NAME) as f:
        county = int(f.readline().strip())
        username = f.readline().strip()
        password = f.readline().strip()

    if not username or not password:
        raise Exception

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
                        .format(county,username,password)).strip()
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



def save_browser_preference():
    while 1:
        choice = input('\n1) Chrome   2) Edge   3) Firefox\n'
                       'Choose your browser preference: ').strip()

        _driver = None
        browser = None
        if choice == '1':
            _driver = webdriver.Chrome(CHROME_DRIVER)
            browser = Browser.CHROME
        elif choice == '2':
            _driver = webdriver.Edge(EDGE_DRIVER)
            browser = Browser.EDGE
        elif choice == '3':
            _driver = webdriver.Firefox(FIREFOX_DRIVER)
            browser = Browser.FIREFOX
        else:
            print('Invalid input. Try again.\n')
            continue
        break

    with open('files/' + BROWSER_CHOICE_FILE_NAME, mode='w') as f:
        f.write(str(browser.value))

    return _driver


def read_browser_file():
    with open('files/' + BROWSER_CHOICE_FILE_NAME, mode='r') as f:
        browser = f.readline().strip()

    if browser == str(Browser.CHROME.value):
        return webdriver.Chrome(CHROME_DRIVER)
    elif browser == str(Browser.EDGE.value):
        return webdriver.Edge(EDGE_DRIVER)
    elif browser == str(Browser.FIREFOX.value):
        return webdriver.Firefox(FIREFOX_DRIVER)
    else:
        print('Browser preference file has invalid data. Lets overwrite it\n')
        os.remove('files/'+BROWSER_CHOICE_FILE_NAME)
        return save_browser_preference()


def rank_aspect_values():
    numeric = []
    while 1:
        user_input = input('\n{}) Human {}) Beast   {}) Knowledge {}) Destruction   {}) Order {}) Chaos   '
                                '{}) Nature {}) Corruption\n'
                           'Select the 4 aspects that you prefer, in preference order (spaces between like: 7 2 5 4): '
                           .format(Aspect.HUMAN.value, Aspect.BEAST.value,Aspect.KNOWLEDGE.value,Aspect.DESTRUCTION.value,
                                   Aspect.ORDER.value, Aspect.CHAOS.value,Aspect.NATURE.value,Aspect.CORRUPTION.value)).strip()

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
        for line in f:
            line = line.strip()
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

    if len(value_dict) != 8:
        raise Exception

    return value_dict


def read_or_rank_aspect_values() -> Dict[Aspect, int]:
    if not path.exists('files/' + ASPECTS_FILE_NAME):
        rank_aspect_values()

    try:
        return read_aspect_values_from_file()
    except Exception:
        print('Aspect preferences file has invalid data. Lets overwrite it')
        rank_aspect_values()
        return read_aspect_values_from_file()


def get_new_action() -> bool:
    while 1:
        print('1) ManHunt   2) Grotto   3) Tavern   4) Graveyard   5) Heal   0) Exit')
        user_in = input('choose an action: ').strip()

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
        target = input('  1) Farm   2) Village   3) Small Town   4) City   5) Metropolis   0) Cancel\n'
                      '  Choose category: ').strip()

        if not target.isnumeric():
            print('  Invalid input')
            continue

        target = int(target)
        if target > 5:
            print('  Invalid input\n')
            continue

        if target == 0:
            print()
            return None

        amount = input('  How many? ').strip()
        if not amount.isnumeric():
            print('  Invalid input\n')
            continue

        if amount == '0':
            print()
            return None

        return ManHuntAction(ManHuntTarget(target), int(amount))


def take_grotto_input():
    while 1:
        difficulty = input('  1) {}   2) {}   3) {}   0) Cancel\n' 
                           '  Choose difficulty: '.format(Difficulty.EASY.name, Difficulty.MEDIUM.name,
                                                          Difficulty.DIFFICULT.name)).strip()
        if not difficulty.isnumeric():
            print('  Invalid input')
            continue

        difficulty = int(difficulty)
        if difficulty > 3:
            print('  Invalid input\n')
            continue

        if difficulty == 0:
            print()
            return None

        amount = input('  How many? ').strip()
        if not amount.isnumeric():
            print('  Invalid input\n')
            continue

        if amount == '0':
            print()
            return None

        return GrottoAction(Difficulty(difficulty),int(amount))


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


def click(element: WebElement):
    sleep(CLICK_DELAY)
    element.click()


if __name__ == '__main__':
    run()
