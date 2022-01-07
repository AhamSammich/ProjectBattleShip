import os
import webbrowser
import pygame as pg
import logging as lg
import random as rd
import bsgui as ui
import bsvessels as vs
import gamerbase as gb
from typing import Union
from gamerbase import GameState as State, Log, SkillType as SkType

pg.mixer.init()
lg.basicConfig(level=lg.INFO, format=' %(asctime)s - %(levelname)s - %(message)s')


class Target:
    """
    Contains attributes used for tracking position and progress.
    Controls sound effects for general firing sequence.
    """
    HIT_COLOR = ui.Display.RGB_RED
    MISS_COLOR = ui.Display.RGB_WHITE
    NO_COLOR = ui.Display.RGB_DARK_BLUE

    LAUNCH_SOUND = pg.mixer.Sound('Sounds/missile.wav')
    HIT_SOUND = pg.mixer.Sound('Sounds/hit2.wav')
    SINK_SOUND = pg.mixer.Sound('Sounds/explosion.mp3')

    def __init__(self, x=0, y=0, size=50, xy_offset=(50, 50)):
        # x, y = Target column, row
        self._x = x
        self._y = y
        self._coord = (x, y)
        # Position is the Target's alphanumeric reference, e.g. (0, 0) = "A1".
        # ASCII values, ord() and chr() are used for this conversion.
        self._name = self.convert_coord(x, y)
        # Box is a pygame rectangle for use with the user interface.
        self._box = ui.Box(
            dimensions=(x * size + (x + xy_offset[0]), y * size + (y + xy_offset[1]), size, size),
            box_name=self.name
        )
        self._checked = False
        self._result = ''
        self.ship: Union[vs.Vessel, None] = None

    def __repr__(self):
        return self.name

    @staticmethod
    def convert_coord(x, y):
        return f'{chr(x + 97).upper()}{y + 1}'

    def attack(self) -> bool:
        """Executed when Player has selected a Target. Returns 'True' on hit."""
        if self.occupied:
            self.ship.hit()
            self.result = 'HIT'
            self.box.color2 = self.HIT_COLOR
            if self.ship.sunk:
                ui.DisplayData.TARGET_INTER.text = f"{self.ship} SUNK!"
            else:
                ui.DisplayData.TARGET_INTER.text = f'{self.ship} {self.result} @ {self}...'
        else:
            self.result = 'MISS'
            self.box.color2 = self.MISS_COLOR
            # Prioritize hit/sunk messages
            if ('HIT' or 'SUNK') not in ui.DisplayData.TARGET_INTER.text:
                ui.DisplayData.TARGET_INTER.text = f'{self.result} @ {self}...'
        return self.occupied

    def reset(self):
        self.result = ''

    @property
    def checked(self) -> bool:
        return bool(self.result)

    @property
    def result(self) -> str:
        return self._result

    @result.setter
    def result(self, hit_miss: str):
        self._result = hit_miss
        self.box.flash = False
        match hit_miss:
            case 'HIT':
                self.box.color2 = self.HIT_COLOR
            case 'MISS':
                self.box.color2 = self.MISS_COLOR
            case _:
                self._result = ''
                self.box.color2 = None

    @property
    def ship(self) -> vs.Vessel:
        return self._ship

    @ship.setter
    def ship(self, ship: vs.Vessel):
        self._ship = ship
        self.box.color3 = ui.Display.RGB_YELLOW if ship else None

    @property
    def occupied(self) -> bool:
        return bool(self.ship)

    # ----- Read-only Properties -----

    @property
    def name(self) -> str:
        return self._name

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._y

    @property
    def coord(self) -> tuple[int, int]:
        return self._coord

    @property
    def box(self) -> ui.Box:
        return self._box


class Board:
    """This represents the field where ships are placed.
    The board is composed of a collection of pygame rectangles to form a grid.
    """
    ORDINAL = ((1, 0), (0, 1), (-1, 0), (0, -1))
    SQR_SIZE = 50
    GRID_SIZE = 10
    GRID_POS = (50, 50)
    SEARCH_DIR = 0
    DETECTED: Target = None

    def __init__(self, player: gb.Player):
        self.player = player
        self.positions = {}
        self.grid = []
        self.headers = []
        self.target_locked = False

    def __repr__(self):
        return f"{self.player}'s Board"

    def init_targets(self, sqr_size=SQR_SIZE, grid_size=GRID_SIZE, grid_pos=GRID_POS):
        """Generates a list of the target boxes to pass to the function for drawing the
        pygame window.
        """
        # Update constants if other sizes specified in parameters.
        if sqr_size != self.SQR_SIZE:
            self.SQR_SIZE = sqr_size
        if grid_size != self.GRID_SIZE:
            self.GRID_SIZE = grid_size
        if grid_pos != self.GRID_POS:
            self.GRID_POS = grid_pos

        for row_y in range(grid_size):
            for col_x in range(grid_size):
                pos = Target(x=col_x, y=row_y, size=sqr_size, xy_offset=grid_pos)
                self.positions.setdefault(pos.name, pos)  # key='A1', value=Target(object)

        boxes = [target.box for target in self.positions.values()]
        self.grid = boxes
        self.create_headers(grid_pos)

    def create_headers(self, grid_pos):
        """Generates headers to display over grid."""
        offset_x, offset_y = map(lambda x: x + 10, grid_pos)
        font, color = ui.Display.FONT, ui.Display.FONT_COLOR

        # Create list of row headings and positions for drawing(WINDOW.blits).
        rx = offset_x - self.SQR_SIZE * 0.75
        row_header: list[pg.Surface] = [font.render(str(y + 1), True, color)
                                        for y in range(self.GRID_SIZE)]
        row_header_pos: list[tuple] = [(rx, self.SQR_SIZE * y + (y + offset_y))
                                       for y in range(self.GRID_SIZE)]

        row_head = [(row, pos) for row, pos in zip(row_header, row_header_pos)]
        self.headers.append(row_head)

        # Create list of column headings/positions.
        ry = offset_y - self.SQR_SIZE * 0.75
        col_header: list[pg.Surface] = [font.render(chr(x + 97), True, color)
                                        for x in range(self.GRID_SIZE)]
        col_header_pos: list[tuple] = [(self.SQR_SIZE * x + (x + offset_x), ry)
                                       for x in range(self.GRID_SIZE)]

        col_head = [(col, pos) for col, pos in zip(col_header, col_header_pos)]
        self.headers.append(col_head)

    def select_row(self, target=None) -> list[Target]:
        if target is None:
            target = self.select_target()
        if target is not None:
            positions = [
                Target.convert_coord((target.x + x) % self.GRID_SIZE, target.y) for x in range(self.GRID_SIZE)
            ]
            return [self.positions[pos] for pos in positions]

    def select_column(self, target=None) -> list[Target]:
        if target is None:
            target = self.select_target()
        if target is not None:
            positions = [
                Target.convert_coord(target.x, (target.y + y) % self.GRID_SIZE) for y in range(self.GRID_SIZE)
            ]
            return [self.positions[pos] for pos in positions]

    def select_target(self, random=False, target_list=()) -> Target:
        """
        Target selected from board positions or specified list.
        Selection may be random or provided by mouse input.
        """
        selected = None
        targets = list(target_list) if target_list else list(self.positions.values())

        if random:
            selected = rd.choice(targets)
        else:
            for target in targets:
                if ui.mouse_over(target.box):
                    selected = target
        return selected

    @Log.call_log
    def comp_target(self, comp_level: int):
        selected = rd.choice(list(self.positions.values()))
        if comp_level == 3 or (comp_level == 2 and self.target_locked):
            hits = [target for target in self.positions.values() if target.result == 'HIT']
            target_found = self.search_target(hits, comp_level)

            if target_found:
                selected = target_found
            else:
                self.target_locked = False
        return selected

    @Log.call_log
    def search_target(self, hit_list: list[Target], comp_level: int) -> Target:
        detected = [target for target in hit_list if not target.ship.sunk]

        while detected:
            target = rd.choice(detected)
            calculated = self.calculate_target(target.coord)
            if calculated:
                return calculated
            elif comp_level == 3:  # Comp difficulty = 'Hard'
                detected.remove(target)
                lg.debug(f'Reassessing...(detected={detected})')
                continue
            else:
                break

    @Log.call_log
    def calculate_target(self, coord: tuple[int, int], rand_dir=False) -> Target:
        attempts_remaining = 4
        while attempts_remaining:
            dx, dy = rd.choice(list(self.ORDINAL)) if rand_dir else self.ORDINAL[self.SEARCH_DIR]
            x, y = coord

            # Adjust range to compensate for edge of board.
            nx = (x + dx) % self.GRID_SIZE
            ny = (y + dy) % self.GRID_SIZE

            calc_target = self.positions[Target.convert_coord(nx, ny)]
            lg.debug(f'calc_target={calc_target} (coord={coord}, direction={self.SEARCH_DIR})')

            if calc_target.checked:
                d = self.SEARCH_DIR
                self.SEARCH_DIR = (d + 1) % 4
                attempts_remaining -= 1
                lg.debug(f'Target checked. Adjusting... (direction={self.SEARCH_DIR}, attempts={attempts_remaining})')
                continue

            return calc_target

    @property
    def target_locked(self) -> bool:
        return self._locked

    @target_locked.setter
    def target_locked(self, is_locked):
        self._locked = is_locked


# ========== FLEET CREATION AND POSITIONING METHODS ==========

def deploy_fleet(board: Board, player: gb.Player) -> list[vs.Vessel]:
    """
    Creates new Player attributes to link player to board and ships.
    Initializes Vessel instances.
    Sets image size and adds 'player' attribute to the Vessel.
    """
    player.__setattr__('board', board)
    player.__setattr__(
        'fleet', {'Carrier': vs.Carrier(),
                  'Cruiser': vs.Cruiser(),
                  'Destroyer': vs.Destroyer(),
                  'Submarine': vs.Submarine(),
                  'Frigate': vs.Frigate()
                  }
    )
    fleet = player.fleet.values()
    height = board.SQR_SIZE
    for ship in fleet:
        ship.__setattr__('player', player)
        ship.name = f'{player.name[0]}{ship.name}'
        width = height * ship.size + ship.size
        ship.image = pg.transform.scale(ship.image, (width, height))

        # ----- Assign Special from skills module -----
        ship.__setattr__('special', Special(ship))

    return list(fleet)


def place_ship(board: Board, fleet, rotate=False) -> bool:
    """
    Places ships on the board.
    Returns boolean to continue/break setup loop in the main game loop.
    """
    fleet_deployed = False
    ships = [ship for ship in fleet if ship.image not in ui.DisplayData.IMAGES]
    ship = ships[0]
    vertical = ship.image.get_width() < ship.image.get_height()

    # Rotate image without placing the ship.
    if rotate:
        angle = 90 if vertical else -90
        ship.image = pg.transform.rotate(ship.image, angle)
        return fleet_deployed

    target = board.select_target()
    if target is not None:
        if vertical:
            positions = [Target.convert_coord(target.x, target.y + y) for y in range(ship.size)]
        else:
            positions = [Target.convert_coord(target.x + x, target.y) for x in range(ship.size)]

        while True:
            try:
                targets = [board.positions[pos] for pos in positions]
            except KeyError:
                lg.info('Insufficient space. Reselect')
                break
            else:
                pos_occupied = [target.occupied for target in targets]
                if any(pos_occupied):
                    lg.info(f'Insufficient space. Reselect.')
                    break
                # Append to global lists for drawing images in game window.
                ui.DisplayData.IMAGES.append(ship.image)
                ui.DisplayData.POSITIONS.append(target.box)

                ship.deploy(targets)
                for target in targets:
                    target.ship = ship
                    target.reset()
            try:
                assert len(ship.position) == ship.size
            except AssertionError:
                lg.error(f'{ship.type.upper()} PLACEMENT ERROR. ({board.player})')
            else:
                break
    return all([ship.position for ship in fleet])  # True if all ships placed.


def place_random(board, fleet):
    for ship in fleet:
        # 50% chance to rotate image.
        if rd.randint(0, 1):
            ship.image = pg.transform.rotate(ship.image, 90)

        placing = True
        while placing:
            target = board.select_target(random=True)
            vertical = ship.image.get_width() < ship.image.get_height()

            if vertical:
                positions = [Target.convert_coord(target.x, target.y + y) for y in range(ship.size)]
            else:
                positions = [Target.convert_coord(target.x + x, target.y) for x in range(ship.size)]

            lg.debug(f'place_random: ship={ship.type}, target={target}, positions={positions}')
            attempt_remaining = True
            while True:
                try:
                    targets = [board.positions[pos] for pos in positions]
                except KeyError:
                    if attempt_remaining:
                        attempt_remaining = False
                        positions = reattempt_placement(target, ship)
                        continue
                    else:
                        lg.info(f'Insufficient space. Reselecting...')
                        break
                else:
                    pos_occupied = [target.occupied for target in targets]
                    if any(pos_occupied):
                        if attempt_remaining:
                            attempt_remaining = False
                            positions = reattempt_placement(target, ship)
                            continue
                        else:
                            lg.info(f'Insufficient space. Reselecting...')
                            break
                    # Appends to global lists if player selected random placement.
                    if board.player.name.startswith('Player'):
                        ui.DisplayData.IMAGES.append(ship.image)
                        ui.DisplayData.POSITIONS.append(target.box)

                    ship.deploy(targets)
                    for target in targets:
                        target.ship = ship
                        target.reset()
                    try:
                        assert len(ship.position) == ship.size
                    except AssertionError:
                        lg.error(f'{ship.type.upper()} PLACEMENT ERROR. ({board.player})')
                        lg.error(f'place_random: target.ship.position={target.ship.position}')
                    else:
                        placing = False
                        break


def reattempt_placement(target, ship) -> list:
    """Rotate ship image and regenerate position list."""
    lg.info(f'No space. Rotating. Reattempting...')
    ship.image = pg.transform.rotate(ship.image, 90)
    vertical = ship.image.get_width() < ship.image.get_height()
    if vertical:
        positions = [Target.convert_coord(target.x, target.y + y) for y in range(ship.size)]
    else:
        positions = [Target.convert_coord(target.x + x, target.y) for x in range(ship.size)]
    return positions


def remove_ship(board: Board, target: Target):
    if target is not None:
        if target.occupied:
            ship = target.ship

            for position in ship.position:
                # Reset Target object attributes.
                position.ship = None
                # Remove position from global list for drawing.
                if position.box in ui.DisplayData.POSITIONS:
                    ui.DisplayData.POSITIONS.remove(position.box)

            for target in ship.position:
                target.reset()
            ship.position.clear()  # Reset Vessel object attribute.
            if ship.image in ui.DisplayData.IMAGES:
                ui.DisplayData.IMAGES.remove(ship.image)  # Remove image from global.
            lg.info(f"Removed {board.player}'s {ship.type}({ship.name}) @ {target}.")

            try:
                assert len(ui.DisplayData.IMAGES) == len(ui.DisplayData.POSITIONS)
            except AssertionError:
                lg.error(f'{ship.type} REMOVAL ERROR. ({board.player})')


# ========== END GAME METHODS ==========

def clear_ships(board: Board):
    """Clear all targets on the board."""
    ui.DisplayData.IMAGES.clear()
    ui.DisplayData.POSITIONS.clear()
    for target in board.positions.values():
        if target.ship:
            target.ship.redeploy()
            target.ship.special.reset()
        target.ship = None
    lg.info(f"All ships removed from {board.player}'s board.")


def clear_boards(boards: list[Board]):
    """Resets both boards, all ships and messages."""
    for board in boards:
        clear_ships(board)
        for target in board.positions.values():
            target.reset()

    for msg in ui.DisplayData.get_messages():
        msg.text = '' if msg is not ui.DisplayData.TITLE_MSG else msg.text

    ui.DisplayData.PLAYER_MSG.text = 'PLAYER'
    ui.DisplayData.COMP_MSG.text = 'COMP'
    ui.DisplayData.TURN_MSG.text = 'TURN 1'


def victory(player_fleet: list[vs.Vessel], enemy_fleet: list[vs.Vessel]) -> bool:
    """
    Checks if all players' ships are sunk.
    Returns boolean to continue/break main loop.
    """
    end_game = False

    if all([ship.sunk for ship in player_fleet]):
        ui.DisplayData.END_MSG.text = 'DEFEAT. All player ships sunk...'
        defeat_sound = pg.mixer.Sound('Sounds/dies-irae.wav')
        defeat_sound.play()
        pg.time.delay(1000)
        end_game = True
    elif all([ship.sunk for ship in enemy_fleet]):
        ui.DisplayData.END_MSG.text = 'VICTORY! All enemy ships sunk!'
        victory_sound = pg.mixer.Sound('Sounds/victory-fanfare.wav')
        victory_sound.play()
        pg.time.delay(1000)
        end_game = True

    return end_game


# ========== MAIN LOOP METHODS ==========

# @Log.call_log
def fire(board: Board, target=None, comp_fire=0, multi=False) -> bool:
    """Returns boolean to indicate successful execution of action to progress game state."""
    launched = False
    if comp_fire and target is None:
        target = board.comp_target(comp_fire)  # comp_fire = comp_level
    elif target is None:
        target = board.select_target()

    if target is not None:
        if not target.checked:
            launched = True
            if not multi:  # Skip launch sound effect during multiple shots to minimize lag.
                Target.LAUNCH_SOUND.play()
                pg.time.delay(1000)
            if target.attack():
                # Ship has been hit at the selected target.
                Target.HIT_SOUND.play()
                pg.time.delay(1000)
                ship: vs.Vessel = target.ship
                # Trigger any applicable passive skills.
                Special.trigger_passive(ship, board)

                if comp_fire:
                    if target is board.DETECTED:
                        board.DETECTED = None
                    board.target_locked = True
                if ship.sunk:
                    Target.SINK_SOUND.play()
                    pg.time.delay(1000)
                    ship.special.downtime = -1  # Sets 'ready' attribute to False.
                    board.target_locked = False
                    # Ensure sunk ship indicates hit. Color may not be set due to Submarine repositioning.
                    for tgt in ship.position:
                        tgt.result = 'HIT'
                    if not comp_fire:
                        # Reveal ship on the opponent's board.
                        ui.DisplayData.IMAGES.append(ship.image)
                        ui.DisplayData.POSITIONS.append(ship.position[0].box)
            # else:  # Target missed
            #     if not multi:  # Skip miss sound effect during multiple shots to minimize lag.
        else:
            lg.info(f'Target checked. ({target.result} @ {target})')
            if target is board.DETECTED:
                board.DETECTED = None  # Prevent infinite looping
    pg.display.flip()
    return launched


def switch_players(grid_data: list[list], game: gb.GameFlow):
    """Alternate turns and update messages. Redraw the game window."""
    # Messages updated for the player's turn.
    if game.state is State.COMP:
        ui.DisplayData.PLAYER_MSG.text = f'{ui.DisplayData.SKILL_INTER.text}'
        ui.DisplayData.P_TGT_MSG.text = f'{ui.DisplayData.TARGET_INTER.text}'
        ui.DisplayData.ACTION_MSG.text = 'Left-click to select a target --- OR --- Select a ship to activate special'
        Special.turnover()

    # Messages updated for the player's turn.
    else:
        ui.DisplayData.COMP_MSG.text = f'{ui.DisplayData.SKILL_INTER.text}'
        ui.DisplayData.C_TGT_MSG.text = f'{ui.DisplayData.TARGET_INTER.text}'

    # Update common messages
    ui.DisplayData.TURN_MSG.text = f'TURN {game.turn}'
    ui.DisplayData.TARGET_INTER.text = ''
    ui.DisplayData.SKILL_INTER.text = ''

    # Draw the game boards.
    ui.draw_grids(*grid_data)
    # Draw ships and messages.
    ui.DisplayData.draw()
    pg.display.flip()


@Log.call_log
def start_screen(game: gb.GameFlow, clock):
    game.break_flow(State.START)
    while game.state is State.START:
        clock.tick(ui.Display.FPS)
        ui.DisplayData.draw_start()
        start_btn = ui.DisplayData.START_BUTTON

        for event in pg.event.get():
            if event.type == pg.QUIT:
                game.end_flow()

            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if ui.mouse_over(start_btn):
                        game.break_flow(State.SETUP)
                    elif ui.mouse_over(ui.DisplayData.INFO_BUTTON):
                        webbrowser.open_new_tab(os.path.join('Misc', 'info.html'))

            if event.type == pg.KEYDOWN:
                keys_pressed = pg.key.get_pressed()

                if keys_pressed[pg.K_RETURN]:
                    game.break_flow(State.SETUP)
                elif keys_pressed[pg.K_ESCAPE]:
                    game.end_flow()

        pg.display.flip()


def main():
    """This is the main game loop."""
    # Track game progression.
    clock = pg.time.Clock()
    game = gb.GameFlow()
    ui.DisplayData.TURN_MSG.text = 'TURN 1'

    start_screen(game, clock)

    # Create Player and Comp.
    player1 = gb.Player()
    player1.set_opponent(gb.Comp(difficulty=3))

    # Create Player board.
    board1 = Board(player1)
    board1.init_targets(sqr_size=45, grid_pos=(ui.Display.WIDTH / 2 + 80, 100))

    # Create Player ships.
    player_fleet = deploy_fleet(board1, player1)

    # Set opponent.
    player2 = player1.opp
    player2.set_opponent(player1)

    # Create Comp board.
    board2 = Board(player2)
    board2.init_targets(sqr_size=45, grid_pos=(70, 100))

    # Create Comp ships.
    deploy_fleet(board2, player2)
    enemy_fleet = list(player2.fleet.values())
    place_random(board2, enemy_fleet)

    # Organize grid data for passing to the interface. Show initial setup instructions.
    grid_data = [board1.grid, board2.grid, board1.headers, board2.headers]
    ui.DisplayData.RESULT_MSG.text = 'Left-click to place ship on the grid. --- Right-click on ship to remove it.'
    ui.DisplayData.ACTION_MSG.text = 'BACKSPACE to clear all ships. -- ENTER to place all randomly.-- ' \
                                     'SPACEBAR to rotate 90 degrees.'

    activated = None  # Ship selected for activating Special.
    while game.state is not State.QUIT:
        clock.tick(ui.Display.FPS)

        if game.state is State.COMP:
            activated = Special.charge(board2, comp_fleet=tuple(enemy_fleet))
            if activated:
                turn_end = Special.discharge(board1, activated, comp_fire=player2.level)
                activated = None
            else:
                turn_end = fire(board1, board1.DETECTED, comp_fire=player2.level)
            if turn_end:
                switch_players(grid_data, game)
                game.progress_flow()
                Special.check_ready(player_fleet)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                game.end_flow()

            # ----- PLAYER INTERACTION -----
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1 and ui.mouse_over(ui.DisplayData.INFO_BUTTON):
                    webbrowser.open_new_tab(os.path.join('Misc', 'info.html'))

                if game.state is State.PLAY:
                    if event.button == 1:  # LEFT-CLICK
                        Special.check_ship(board1.grid, player_fleet)
                        activated = Special.charge(board1, activated)
                        turn_end = fire(board2)
                        if turn_end:
                            switch_players(grid_data, game)
                            game.progress_flow()

                    elif event.button == 3:
                        turn_end = Special.discharge(board2, activated)
                        if turn_end:
                            activated = None
                            switch_players(grid_data, game)
                            game.progress_flow()

                if game.state is State.SETUP:
                    if event.button == 1:  # LEFT-CLICK
                        finished = place_ship(board1, player_fleet)
                        if finished:
                            ui.DisplayData.RESULT_MSG.text = 'Player fleet deployed. Ready to attack...'
                            ui.DisplayData.ACTION_MSG.text = \
                                'Left-click to select a target --- OR --- Select a ship to activate special'
                            game.progress_flow(start=State.PLAY)

                    elif event.button == 3:  # RIGHT-CLICK
                        pos = board1.select_target()
                        remove_ship(board1, pos)

            elif event.type == pg.KEYDOWN:
                keys_pressed = pg.key.get_pressed()

                # Displays window when game ends until any key is pressed.
                if game.state is State.END:
                    if keys_pressed[pg.K_ESCAPE]:
                        game.end_flow()
                    elif keys_pressed[pg.K_SPACE]:
                        clear_boards([board1, board2])
                        place_random(board2, enemy_fleet)
                        game.reset()

                if game.state is State.SETUP:
                    if keys_pressed[pg.K_BACKSPACE] and ui.DisplayData.POSITIONS:
                        # Removes all placed ships.
                        clear_ships(board1)

                    if keys_pressed[pg.K_RETURN]:
                        # Clear board, place all ships randomly, then exit setup loop.
                        clear_ships(board1)
                        place_random(board1, player_fleet)
                        ui.DisplayData.RESULT_MSG.text = 'Player fleet deployed. Ready to attack...'
                        ui.DisplayData.ACTION_MSG.text = \
                            'Left-click to select a target --- OR --- Select a ship to activate special'
                        game.progress_flow(start=State.PLAY)

                    if keys_pressed[pg.K_SPACE]:
                        _ = place_ship(board1, player_fleet, rotate=True)

        # Draw the game boards.
        ui.draw_grids(*grid_data)
        # Draw ships and messages.
        ui.DisplayData.draw()
        # Display ship when placing fleet.
        if game.state is State.SETUP:
            ships = [ship.image for ship in player_fleet if ship.image not in ui.DisplayData.IMAGES]
            ui.draw_images([ships[0]], [pg.mouse.get_pos()])
        pg.display.flip()

        if game.state is State.WAIT:
            # Check for victory conditions.
            if victory(player_fleet, enemy_fleet):
                game.break_flow(State.END)
                ui.DisplayData.ACTION_MSG.text = 'Press ESC to exit game --- OR --- Press SPACEBAR to play again'
            game.progress_flow()

    lg.info('GAME END. Thank you for playing!')


# ========== SPECIALS ==========


class Special(gb.GameSkill):
    """
    Skills assigned based on ship-type during game initialization.
    Sequence of execution: charge -> prep_data -> discharge -> restore_data.
    """
    # Dictionary provides attributes for each skill.
    SKILLS = {'Cruiser': {'info': 'Fires missiles with %chance to hit surrounding targets. (max 5 shots)',
                          'name': 'Missile Salvo',
                          'type': SkType.INSTANT,
                          'cooldown': 1,
                          'chance': 100,
                          'func': 'missile_salvo',
                          'sound': pg.mixer.Sound('Sounds/rapid-missile-launch.wav')
                          },
              'Destroyer': {'info': '(PASSIVE) %-chance to counter-detect a submarine after being hit.',
                            'name': 'Sonar Blast',
                            'type': SkType.PASSIVE,
                            'cooldown': -1,
                            'chance': 75,
                            'func': 'sonar_blast',
                            'sound': pg.mixer.Sound('Sounds/sonar2.wav')
                            },
              'Submarine': {'info': '(PASSIVE) %-chance to evade detection after being hit.',
                            'name': 'Countermeasures',
                            'type': SkType.PASSIVE,
                            'cooldown': -1,
                            'chance': 75,
                            'func': 'countermeasures',
                            'sound': pg.mixer.Sound('Sounds/submarine-travel.mp3')
                            },
              'Frigate': {'info': 'Deploys charge with a %chance to hit a submarine. (max 3 charges)',
                          'name': 'Depth Charge',
                          'type': SkType.INSTANT,
                          'cooldown': 2,
                          'chance': 100,
                          'func': 'depth_charge',
                          'sound': pg.mixer.Sound('Sounds/depth.wav')
                          },
              'Carrier': {'info': "Fires shot perpendicular to ship's orientation across entire row/column.",
                          'name': 'EM Railgun',
                          'type': SkType.INSTANT,
                          'cooldown': 6,
                          'chance': 100,
                          'func': 'em_railgun',
                          'sound': pg.mixer.Sound('Sounds/railgun.mp3')
                          }
              }

    def __init__(self, ship: vs.Vessel):
        args = self.SKILLS[ship.type]
        super().__init__(name=args['name'],
                         description=args['info'],
                         cooldown=args['cooldown'],
                         success_rate=args['chance']
                         )
        self.func = getattr(Special, args['func'])
        self.sound = args['sound']
        self._ship = ship

        self._type = args['type']
        if args['type'] is SkType.PASSIVE:
            self.disable_ready()

    @Log.call_log
    def __call__(self, *args, **kwargs):
        self.activate(*args, **kwargs)

    def check(self):
        ship = self.ship
        if ship.sunk:
            ui.DisplayData.RESULT_MSG.text = f'{ship} is sunk.'
            self.disable_ready()
        elif not ship.special.ready and ship.special.type is not SkType.PASSIVE:
            ui.DisplayData.RESULT_MSG.text = f'{ship.special} down for {ship.special.downtime} more turn(s).'
        else:
            ui.DisplayData.RESULT_MSG.text = f'{ship} --- {ship.special.description}'

    def reset(self):
        self.downtime = 0
        self.uptime = 0
        if self.type is SkType.PASSIVE:
            self.disable_ready()

    # ----- Read-only Properties -----

    @property
    def type(self):
        return self._type

    @property
    def ship(self):
        return self._ship

    # ----- Static Methods called in main function -----

    @staticmethod
    def charge(board: Board, ship=None, comp_fleet=()) -> vs.Vessel:
        # Reset any previous selections
        if ship:
            Special.restore_data(ship)

        # Return random selection for the Comp player
        if comp_fleet:
            ready = [ship for ship in list(comp_fleet)
                     if all([ship.special.ready, ship.special.type is SkType.INSTANT, not ship.sunk])]
            return rd.choice(ready) if ready else None

        # Player selects target from the board
        else:
            target = board.select_target()
        try:
            if all([target.occupied,
                    target.ship.special.type is SkType.INSTANT,
                    not target.ship.sunk,
                    not target.ship.special.downtime
                    ]):
                ship = target.ship
                Special.prep_data(ship)
                ui.DisplayData.ACTION_MSG.text += ' (Right-click on target to fire.)'
        except AttributeError:  # Return None if no target is selected.
            if ship:
                Special.restore_data(ship)
                ship = None
        return ship

    @staticmethod
    def prep_data(ship: vs.Vessel):
        """Set associated variables and messages for executing the Special."""
        for target in ship.position:
            target.box.active = True

        if ship.type == 'Carrier':
            ui.DisplayData.ACTION_MSG.text = f'{ship.type} firing {ship.special}!'
            if ship.align is vs.Align.VERTICAL:
                ui.Display.EXPAND_ROW = True
            else:
                ui.Display.EXPAND_COL = True

        elif ship.type == 'Cruiser':
            ui.DisplayData.ACTION_MSG.text = f'{ship.type}  firing  {ship.special}!'

        elif ship.type == 'Frigate':
            ui.DisplayData.ACTION_MSG.text = f'{ship.type}  deploying  {ship.special}!'

    @staticmethod
    def discharge(board: Board, ship=None, comp_fire=0) -> bool:
        launched = False
        comp_chance = rd.randint(1, 100) < comp_fire * 25
        if ship:
            if comp_fire and comp_chance:
                if board.DETECTED:
                    target = board.DETECTED
                    board.DETECTED = None
                else:
                    target = board.comp_target(comp_fire)
            elif not comp_fire:
                target = board.select_target()
            else:
                target = None

            if target is not None:
                launched = True
                ship.special(ship.special, board, target)
            Special.restore_data(ship)
        return launched

    @staticmethod
    def restore_data(ship: vs.Vessel):
        """Restore any variables set by or in preparation for the Special."""
        for target in ship.position:
            target.box.active = False

        if ship.type == 'Carrier':
            ui.Display.EXPAND_COL, ui.Display.EXPAND_ROW = False, False

    @staticmethod
    @Log.call_log
    def trigger_passive(ship: vs.Vessel, *args, **kwargs):
        if ship.type == 'Destroyer':
            ship.special(ship.special, *args, **kwargs)

        elif ship.type == 'Submarine':
            ship.special(ship.special, *args, **kwargs)

    @staticmethod
    def check_ship(grid: list[ui.Box], fleet: list[vs.Vessel]):
        hover_box = ui.get_mouse_over(grid)
        for ship in fleet:
            positions = [target.box for target in ship.position]
            if hover_box in positions:
                ship.special.check()

    @staticmethod
    def check_ready(fleet: list[vs.Vessel]):
        ready_list = [f' {ship.special} ({ship.type})' for ship in fleet if (ship.special.ready and not ship.sunk)]
        if ready_list:
            ui.DisplayData.RESULT_MSG.text = f'SKILLS READY: {str(ready_list)[1:-1]}'

    # ----- Special GameSkill Methods attributed to each ship -----

    def em_railgun(self, board: Board, origin: Target):
        """Fires shot perpendicular to ship's orientation across entire row/column."""
        if self.ship.align is vs.Align.VERTICAL:
            targets = board.select_row(origin)
        else:
            targets = board.select_column(origin)
        self.sound.play()
        pg.time.delay(1000)
        for target in targets:
            _ = fire(board, target=target, multi=True)

    def missile_salvo(self, board: Board, origin: Target):
        """Fires missiles at an area with a (100/n)% chance for the n-th shot after the first. (max 5 shots)"""
        targets = [origin]
        for c in range(1, 5):
            if self.roll_success(self.success_rate / c):
                self.downtime += 1
                add_target = board.calculate_target(origin.coord, rand_dir=True)
                if not add_target:  # Unable to calculate target.
                    continue
                targets.append(add_target)
                origin = add_target

        self.sound.play()
        pg.time.delay(1000)
        for target in targets:
            _ = fire(board, target=target, multi=True)

    def sonar_blast(self, board: Board):
        """75% chance to counter-detect a submarine after being hit."""
        opp_board: Board = board.player.opp.board
        if not self.ship.sunk:
            occ_targets = [target for target in opp_board.positions.values() if target.occupied]
            sub_targets = [target for target in occ_targets
                           if all([target.ship.type == 'Submarine', not target.ship.sunk, not target.checked])]
            if sub_targets:
                self.sound.play()
                pg.time.delay(1000)
                detected = rd.choice(sub_targets)
                detected.box.flash = True
                ui.DisplayData.SKILL_INTER.text = f'{detected.ship} detected @ {detected.box.name}!'
                ui.DisplayData.RESULT_MSG.text = 'ACTIVE PING!'
                opp_board.DETECTED = detected

    def countermeasures(self, board: Board):
        """75% chance randomly repositioning ship and reseting opponent tracker after being hit."""
        if not self.ship.sunk:
            remove_ship(board, self.ship.position[0])
            place_random(board, [self.ship])
            self.sound.play()
            pg.time.delay(1000)

            # Track number of hits accumulated on player ship or sunken ship
            if board.player.name.startswith('Player'):
                for p in range(self.ship.damage):
                    self.ship.position[p].result = 'HIT'

            # Reset miss tracker
            ui.DisplayData.SKILL_INTER.text = f'Dive! Dive! Launching countermeasures!'
            ui.DisplayData.RESULT_MSG.text = 'RADAR JAMMED!'
            for target in board.positions.values():
                if target.result == 'MISS':
                    target.reset()
        else:
            for target in self.ship.position:  # Sets box color, but remains unchecked.
                target.box.color2 = Target.HIT_COLOR  # All ship positions may still be targeted by opponent.

    def depth_charge(self, board: Board, target: Target):
        """Deploys charge with (10 * n-charges)% chance to hit a submarine. (max 50% [5 charges])"""
        # Deploy charge.
        if not self.ship.sunk:
            occ_targets = [target for target in board.positions.values() if target.occupied]
            sub_targets = [target for target in occ_targets
                           if all([target.ship.type == 'Submarine', not target.ship.sunk, not target.checked])]
            if sub_targets:
                self.stacks += int(self.stacks < 3)  # Add 1 stack unless max stacks
                chance = 10 * self.stacks
                ui.DisplayData.SKILL_INTER.text = f'Depth charges deployed. (Total: {self.stacks})'
                detected = rd.choice(sub_targets)
                if self.roll_success(chance=chance):
                    self.sound.play()
                    pg.time.delay(1000)
                    _ = fire(board, target=detected, multi=True)
                    self.stacks -= 1
                    ui.DisplayData.SKILL_INTER.text = f'Depth charge detonated @ {detected.box.name}!'
        # Fire at original target.
        _ = fire(board, target=target)


# ========== CALL MAIN FUNCTION ==========

if __name__ == '__main__':
    main()
