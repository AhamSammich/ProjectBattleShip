from typing import Union
from inspect import getmembers
import pygame as pg
pg.font.init()


class Display:
    """This class contains settings for the display window."""
    WIDTH, HEIGHT = 1200, 800
    WINDOW = pg.display.set_mode((WIDTH, HEIGHT))
    BACKGROUND = pg.image.load('Images/ocean2.jpg')
    BACK_POS = (WIDTH//2 - BACKGROUND.get_width()//2, HEIGHT//2 - BACKGROUND.get_height()//2)
    WIN_COLOR = (20, 70, 180)  # ROYAL BLUE
    pg.display.set_caption('Project BattleShip')
    pg.display.set_icon(pg.image.load('Images/battleship.png'))

    RGB_DARK_BLUE = (0, 20, 75)
    RGB_GREEN = (150, 255, 0)
    RGB_YELLOW = (255, 255, 0)
    RGB_RED = (255, 0, 0)
    RGB_WHITE = (255, 255, 255)
    RGB_BLACK = (0, 0, 0)

    FONT_NAME = 'Fonts/Nau Sea.otf'
    FONT = pg.font.Font(FONT_NAME, 20)
    FONT_COLOR = RGB_WHITE

    FPS = 30
    FRAME = 0
    EXPAND_ROW = False
    EXPAND_COL = False


class MessageBox:
    """This class controls settings for displayed messages."""
    def __init__(self,
                 position=(0.0, 0.0),
                 text='',
                 font=Display.FONT_NAME,
                 size=20,
                 color=Display.FONT_COLOR,
                 background=None
                 ):
        self.position = position
        self.text = text
        self._font = font
        self._size = size
        self.color = color
        self.background = background

    def draw(self):
        message = self.font.render(self.text, True, self.color, self.background)
        Display.WINDOW.blit(message, self.position)

    def center(self, horiz=True, vert=True):
        x, y = self.position
        msg_width, msg_height = self.font.size(self.text)
        win_width, win_height = Display.WIDTH, Display.HEIGHT

        new_x, new_y = x, y
        if horiz:
            new_x = win_width/2 - msg_width/2
        if vert:
            new_y = win_height/2 - msg_height

        self.position = (new_x, new_y)

    def change_font(self, name='', size=0):
        if name:
            self._font = name
        if size > 0:
            self._size = size

    @property
    def font(self) -> pg.font.Font:
        return pg.font.Font(self._font, self._size)

    @property
    def size(self) -> int:
        return self._size


class Box(pg.Rect):
    """This object is the bridge between the interface and the main loop."""
    def __init__(self, dimensions: tuple[float, float, float, float], box_name):
        super().__init__(*dimensions)
        self.name = box_name
        self.flash = False
        self.active = False
        self.color1 = Display.RGB_DARK_BLUE
        self.color2 = None
        self.color3 = None

    def __repr__(self):
        return f'{self.__class__.__name__} {self.name}'


class DisplayData:
    """This class draws the images and text to the window."""
    TITLE = pg.display.get_caption()
    TITLE_POS = (50, 10)
    TITLE_MSG = MessageBox(TITLE_POS, text=TITLE[1], color=Display.RGB_WHITE)

    START_BUTTON = Box((400, 600, 400, 50), 'Start Button')
    START_BUTTON.color1, START_BUTTON.color2 = Display.RGB_DARK_BLUE, Display.RGB_YELLOW
    START_BTN_TEXT = MessageBox((0, START_BUTTON.y), text='PLAY GAME', size=48, color=Display.RGB_WHITE)
    START_BTN_TEXT.center(vert=False)

    IMAGES = []
    POSITIONS = []

    MSG_FONT = 'Fonts/LLPIXEL3.ttf'
    MSG_SIZE = 24
    TARGET_INTER = MessageBox()
    SKILL_INTER = MessageBox()

    # Displayed along bottom
    RESULT_MSG = MessageBox((50, Display.HEIGHT - 100), font=MSG_FONT, size=MSG_SIZE)
    ACTION_MSG = MessageBox((100, Display.HEIGHT - 50), font=MSG_FONT, size=MSG_SIZE)

    # Displayed at center-top
    TURN_MSG = MessageBox((0, 50), text='TURN 1', font=Display.FONT_NAME, color=Display.RGB_YELLOW)
    TURN_MSG.change_font(size=30)

    # Displayed below associated grid
    PLAYER_MSG = MessageBox(
        (70 + Display.WIDTH / 2, Display.HEIGHT - 160), text='PLAYER', font=MSG_FONT, size=MSG_SIZE-2)
    P_TGT_MSG = MessageBox(
        (70 + Display.WIDTH / 2, Display.HEIGHT - 210), font=MSG_FONT, size=MSG_SIZE-2)
    COMP_MSG = MessageBox(
        (70, Display.HEIGHT - 160), text='COMP', font=MSG_FONT, size=MSG_SIZE-2)
    C_TGT_MSG = MessageBox(
        (70, Display.HEIGHT - 210), font=MSG_FONT, size=MSG_SIZE-2)

    # Displayed in center
    END_MSG = MessageBox()
    END_MSG.change_font(name=Display.FONT_NAME, size=56)
    END_MSG.color = Display.RGB_GREEN

    @classmethod
    def get_messages(cls) -> list[MessageBox]:
        # Center messages after text is set.
        cls.TITLE_MSG.position = DisplayData.TITLE_POS
        cls.TITLE_MSG.change_font(size=36)
        for msg in [cls.TURN_MSG, cls.ACTION_MSG, cls.RESULT_MSG, cls.TITLE_MSG]:
            msg.center(vert=False)

        # Set colors and center the end game message.
        if cls.END_MSG.text:
            cls.END_MSG.center()
            cls.END_MSG.background = Display.RGB_DARK_BLUE

            # Set rate for flashing text.
            interval = Display.FPS * 0.75
            cls.END_MSG.color = Display.RGB_YELLOW if Display.FRAME < interval else cls.END_MSG.background

        return [getattr(cls, attr[0]) for attr in getmembers(cls) if attr[0].endswith('_MSG')]

    @classmethod
    def get_data(cls) -> list[list]:
        return [cls.IMAGES, cls.POSITIONS, cls.get_messages()]

    @classmethod
    def draw(cls):
        Display.WINDOW.blits(zip(cls.IMAGES, cls.POSITIONS))
        for msg in cls.get_messages():
            msg.draw()

    @classmethod
    def draw_start(cls):
        """Draws the start screen displayed upon loading."""
        Display.WINDOW.blit(Display.BACKGROUND, Display.BACK_POS)

        cls.TITLE_MSG.change_font(size=64)
        cls.TITLE_MSG.center()
        cls.TITLE_MSG.draw()

        if mouse_over(cls.START_BUTTON):
            cls.START_BUTTON.color1 = Display.RGB_YELLOW
            cls.START_BTN_TEXT.color = Display.RGB_DARK_BLUE
        else:
            cls.START_BUTTON.color1 = Display.RGB_DARK_BLUE
            cls.START_BTN_TEXT.color = Display.RGB_YELLOW
        pg.draw.rect(Display.WINDOW, cls.START_BUTTON.color1, cls.START_BUTTON, 0, 10, 10, 10, 10)
        cls.START_BTN_TEXT.draw()

    @classmethod
    def draw_info(cls):
        pass


def mouse_over(surface: Union[pg.Rect, pg.Surface]) -> bool:
    mouse_pos = pg.mouse.get_pos()
    if type(surface) is pg.Surface:
        surf_rect = surface.get_rect()
    else:
        surf_rect = surface
    return surf_rect.collidepoint(mouse_pos)


def get_mouse_over(rect_list: list[pg.Rect]) -> pg.Rect:
    for rect in rect_list:
        if mouse_over(rect):
            return rect


def draw_images(images: list, positions: list):
    Display.WINDOW.blits(zip(images, positions))


def draw_grids(grid1: list[Box] = None, grid2: list[Box] = None, headers1=None, headers2=None):
    Display.WINDOW.blit(Display.BACKGROUND, Display.BACK_POS)

    if headers1 and headers2:
        for header in headers1+headers2:
            Display.WINDOW.blits(header)

    # Set rate for flashing cursor.
    Display.FRAME = (Display.FRAME + 1) % Display.FPS
    interval = Display.FPS*0.75

    for box in (grid1 + grid2):
        set_color = box.color2 if box.color2 else box.color1

        # Show expanded selection on mouse-over.
        hover_box = box if mouse_over(box) else None
        activate_group(grid2, hover_box)

        # Box will flash on mouse-over.
        if Display.FRAME < interval:
            box_color = Display.RGB_YELLOW \
                if (
                    mouse_over(box)
                    or box.active  # Set by activate_group
                    or box.flash  # Set by external module function
                    ) \
                else set_color
        else:
            box_color = set_color

        if box.color2 or box.active or box.flash or mouse_over(box):
            pg.draw.rect(Display.WINDOW, box_color, box, 0, 10, 10, 10, 10)
        else:
            pg.draw.rect(Display.WINDOW, box_color, box, 2, 10, 10, 10, 10)


def activate_group(grid: list[Box], origin: Box):
    if origin in grid:
        if Display.EXPAND_ROW:
            group = [box for box in grid if box.y == origin.y]
            for box in grid:
                box.active = True if box in group else False
        elif Display.EXPAND_COL:
            group = [box for box in grid if box.x == origin.x]
            for box in grid:
                box.active = True if box in group else False
    else:
        if Display.FRAME == Display.FPS-1:
            for box in grid:
                box.active = False
