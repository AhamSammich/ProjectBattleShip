import random as rd
import os.path
import logging as lg
import pygame as pg
from enum import Enum


class Align(Enum):
    VERTICAL = 1
    HORIZONTAL = 2

    def __repr__(self):
        return self.name


class Vessel:
    """
    This is the base class for the different vessel/ship types.
    Each ship type will have some specific attributes and a special skill.
    @DynamicAttrs
    """
    def __init__(self):
        self._damage = 0
        self._position = []
        self.size = None
        self.name = ''
        self._image_file = None
        self.image = self._image_file
        self._align = None

    def __repr__(self):
        return f'{self.type} ({self.name})'

    def deploy(self, position: list):
        if not self.sunk and len(position) == self.size:
            self._position = position
            self._align = Align.VERTICAL if position[0].x == position[1].x else Align.HORIZONTAL
            lg.debug(f'{self} deployed to {position}. (align={self.align})')

    def hit(self):
        if not self.sunk:
            self._damage += 1

    def redeploy(self):
        self._damage = 0
        self._position.clear()

    @property
    def damage(self) -> int:
        return self._damage

    @damage.setter
    def damage(self, tot_dmg: int):
        if tot_dmg < self.size:
            self._damage = tot_dmg
        else:
            raise ValueError(f'{self} is already sunk.')

    # ----- Read-only properties -----

    @property
    def sunk(self) -> bool:
        return self._damage == self.size

    @property
    def position(self) -> list:
        return self._position

    @property
    def type(self):
        return self.__class__.__name__

    @property
    def align(self):
        return self._align


class Carrier(Vessel):
    """Base for Carrier-type vessels."""
    def __init__(self):
        super().__init__()
        self.size = 5
        self.name = f'CV-{rd.randint(85, 200)}'
        self.image_file = os.path.join('Images', f'ShipCarrierHull.png')
        self.image = pg.image.load(self.image_file)


class Cruiser(Vessel):
    """Base for Cruiser-type vessels."""
    def __init__(self):
        super().__init__()
        self.size = 4
        self.name = f'CG-{rd.randint(85, 200)}'
        self.image_file = os.path.join('Images', f'ShipCruiserHull.png')
        self.image = pg.image.load(self.image_file)


class Submarine(Vessel):
    """Base for Submarine-type vessels."""
    def __init__(self):
        super().__init__()
        self.size = 3
        self.name = f'SS-{rd.randint(810, 1000)}'
        self.image_file = os.path.join('Images', f'ShipSubMarineHull.png')
        self.image = pg.image.load(self.image_file)


class Destroyer(Vessel):
    """Base for Destroyer-type vessels."""
    def __init__(self):
        super().__init__()
        self.size = 3
        self.name = f'DD-{rd.randint(1100, 1500)}'
        self.image_file = os.path.join('Images', f'ShipDestroyerHull.png')
        self.image = pg.image.load(self.image_file)


class Frigate(Vessel):
    """Base for Carrier-type vessels."""
    def __init__(self):
        super().__init__()
        self.size = 2
        self.name = f'FF-{rd.randint(85, 200)}'
        self.image_file = os.path.join('Images', f'ShipFrigateHull.png')
        self.image = pg.image.load(self.image_file)
