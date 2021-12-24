from enum import Enum, unique
from itertools import cycle
from playsound2 import playsound
import random as rd
import asyncio as aio
import logging as lg
import time

"""
This module was built to support this and future projects.
Work in progress.
"""


class Log:
    """
    Using this for debugging during project development.
    """
    LEVEL = lg.INFO
    FORMAT = ' %(asctime)s - %(levelname)s - %(message)s'
    lg.basicConfig(level=LEVEL, format=FORMAT)

    def __init__(self, log_level=LEVEL, log_format=FORMAT):
        self._level = log_level
        self._format = log_format

    @staticmethod
    def call_log(f):
        def call(*args, **kwargs):
            lg.info(f'CALLED {f.__name__}, args={args}, kwargs={kwargs}\n')
            start = time.perf_counter()
            f_return = f(*args, **kwargs)
            end = time.perf_counter()
            lg.info(f'FINISHED {f.__name__}, RETURNED {f_return} [{round(end - start, 2)} second(s)]\n')
            return f_return
        return call


@unique
class GameState(Enum):
    """
    Provides variables for indicating game state.
    With GameFlow, directs execution of code during loops.
    """
    START = -1
    QUIT = 0
    SETUP = 1
    PLAY = 2
    COMP = 3
    END = 4
    WAIT = 5
    VICTORY = 6
    DEFEAT = 7

    def __repr__(self):
        return str(self)


class GameFlow:
    """
    With GameState, directs execution of code during loops.
    """
    TICKS = 0

    def __init__(self,
                 init_state=GameState.START,
                 state_order=(GameState.PLAY, GameState.WAIT, GameState.COMP, GameState.WAIT)):
        self._state = init_state
        self._order = state_order
        self.rotation = state_order
        self._paused = False

    @Log.call_log
    def progress_flow(self, start=None):
        if not self._paused or start:
            if start is not None:
                self.continue_flow(start)
            else:
                self._state = next(self._rotation)
            self.TICKS += 1

    @Log.call_log
    def break_flow(self, set_state: GameState):
        self._state = set_state
        self._paused = True

    def continue_flow(self, from_state: GameState):
        if from_state not in self.order:
            raise KeyError(f'State is not in established flow: {self.order}')
        else:
            self._paused = False
            while self._state is not from_state:
                self.progress_flow()

    @Log.call_log
    def end_flow(self):
        self._state = GameState.QUIT

    def reset(self, to_menu=False):
        self._paused = False
        self.rotation = self.order
        self._state = GameState.START if to_menu else GameState.SETUP
        self.TICKS = 0

    @property
    def rotation(self) -> cycle:
        return self._rotation

    @rotation.setter
    def rotation(self, state_order: tuple[GameState]):
        self._rotation = cycle(list(state_order))
        self._order = state_order

    # ----- Read-only Properties -----
    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def state(self) -> GameState:
        return self._state

    @property
    def order(self) -> tuple[GameState]:
        return self._order

    @property
    def turn(self) -> int:
        return self.TICKS // len(self.order) + 1


class UserProfile:
    def __init__(self, username):
        self.name = username
        self.score = 0
        self.history = {}


class Player:
    """
    This object represent the user and serves as the base for Comp players.
    @DynamicAttrs
    """
    COUNT = 0
    LIST = []

    def __init__(self):
        self.add_player(self)
        self._name = self.__class__.__name__
        self._type = self.__class__.__name__
        self._level = 0
        self._stats = {}
        self._active = False

    def __repr__(self):
        return self.name

    @classmethod
    def add_player(cls, new_player):
        cls.COUNT += 1
        cls.LIST.append(new_player)

    def set_opponent(self, opponent):
        self.__setattr__('opp', opponent)

    @property
    def name(self) -> str:
        return f'{self._name}-{Player.COUNT}'

    @property
    def type(self) -> str:
        return f'{self._type}'

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, player_active):
        self._active = player_active

    @property
    def level(self) -> int:
        return self._level

    @level.setter
    def level(self, difficulty: int):
        self._level = difficulty


class Comp(Player):
    def __init__(self, difficulty=2):
        super().__init__()
        self._level = difficulty


class SkillType(Enum):
    """
    Provides variables for identifying skill types.
    """
    PASSIVE = -1
    INSTANT = 0
    COUNTER = 1
    PERSIST = 2

    def __repr__(self):
        return self.name


class GameSkill:
    """
    Provides a base to inherit for special skills in any game projects.
    Not sure if an abstract base class would be better.
    @DynamicAttrs
    """
    COOLDOWN = []
    ACTIVE = []

    def __init__(self, name='', description='', cooldown=0, success_rate=100, duration=1):
        self.func = None
        self._name = name
        self._description = description
        self._success_rate = success_rate
        self._cooldown = cooldown
        self._duration = duration

        self._downtime = 0
        self._uptime = 0
        self._stacks = 0

    def __repr__(self):
        return self._name

    @classmethod
    def turnover(cls):
        for skill in cls.COOLDOWN:
            skill.downtime -= 1
            if skill.downtime <= 0:
                cls.COOLDOWN.remove(skill)

        for skill in cls.ACTIVE:
            skill.uptime -= 1
            if not skill.uptime:
                cls.ACTIVE.remove(skill)

    def activate(self, *args, **kwargs):
        if self.roll_success():
            self.uptime = self._duration
            self.downtime = self._cooldown
            GameSkill.COOLDOWN.append(self)
            self.func(*args, **kwargs)

    def roll_success(self, chance=0) -> bool:
        if chance:
            return chance >= rd.randint(1, 100)
        else:
            return self.success_rate >= rd.randint(1, 100)

    def disable_ready(self):
        """Prevents 'ready' property from returning True."""
        self._downtime = -1

    def disable_activate(self):
        """Prevents execution of the 'activate' method."""
        self._success_rate = 0

    @property
    def downtime(self) -> int:
        return self._downtime

    @downtime.setter
    def downtime(self, new_val):
        if new_val >= 0:
            self._downtime = new_val

    @property
    def uptime(self) -> int:
        return self._uptime

    @uptime.setter
    def uptime(self, new_val):
        if new_val >= 0:
            self._uptime = new_val

    @property
    def stacks(self) -> int:
        return self._stacks

    @stacks.setter
    def stacks(self, new_val):
        if new_val >= 0:
            self._stacks = new_val

    # ----- Read-only Properties -----

    @property
    def active(self) -> bool:
        return bool(self._uptime)

    @property
    def ready(self) -> bool:
        return not self._downtime

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def success_rate(self) -> int:
        return self._success_rate

    @property
    def cooldown(self) -> int:
        return self._cooldown

    @property
    def duration(self) -> int:
        return self._duration


class GameSound:
    """
    Used to queue and play sounds as game runs.
    Finally found out pygame.mixer exists, so this is no longer used.
    Might be useful for something later.
    """
    def __init__(self):
        self._queue = []
        self._running = False
        self._mute = False

    async def play(self):
        while self.running and self._queue:
            sound = next(self.queue)
            playsound(sound)
            self._queue.remove(sound)
            await aio.sleep(0.1)

    def start_queue(self) -> aio.Task:
        self._running = True
        return aio.create_task(self.play())

    def add_to_queue(self, sound_file: str):
        if not self.mute:
            self._queue.append(sound_file)

    def finish_queue(self):
        self._running = False
        self._queue.clear()

    def get_queue(self) -> list[str]:
        return self._queue

    @staticmethod
    def run_queue(f):
        def run_main():
            main_f = aio.run(f())
            return main_f
        return run_main

    @property
    def mute(self) -> bool:
        return self._mute

    @mute.setter
    def mute(self, mute_set: bool):
        self._mute = mute_set
        if mute_set:
            self._queue.clear()

    @property
    def queue(self) -> iter:
        return cycle(self._queue)

    @queue.setter
    def queue(self, sound_list: list[str]):
        self._queue = sound_list

    # ----- Read-only Properties -----

    @property
    def running(self) -> bool:
        return self._running
