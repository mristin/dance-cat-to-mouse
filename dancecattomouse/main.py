"""Dance collaboratively the cat to catch the mouse."""
import abc
import argparse
import enum
import fractions
import importlib.resources
import itertools
import os.path
import pathlib
import random
import sys
import time
from typing import (
    Optional,
    List,
    Union,
    Tuple,
    Sequence,
    Mapping,
    cast,
    Set,
    Iterator,
)

import pygame
import pygame.freetype
from icontract import require, DBC

import dancecattomouse
import dancecattomouse.events
from dancecattomouse.common import assert_never

assert dancecattomouse.__doc__ == __doc__

PACKAGE_DIR = (
    pathlib.Path(str(importlib.resources.files(__package__)))
    if __package__ is not None
    else pathlib.Path(os.path.realpath(__file__)).parent
)


class Direction(enum.Enum):
    """Specify the walking and looking directions of the actors."""

    NORTH = 1
    EAST = 2
    SOUTH = 3
    WEST = 4


class Media:
    """Represent all the media loaded in the main memory from the file system."""

    def __init__(
        self,
        cat_sprites: Mapping[Direction, Sequence[pygame.surface.Surface]],
        mouse_sprites: Mapping[Direction, Sequence[pygame.surface.Surface]],
        dog_sprites: Mapping[Direction, Sequence[pygame.surface.Surface]],
        font: pygame.freetype.Font,  # type: ignore
        bark_sound: pygame.mixer.Sound,
        bell_sound: pygame.mixer.Sound,
        victory_sound: pygame.mixer.Sound,
    ) -> None:
        """Initialize with the given values."""
        self.cat_sprites = cat_sprites
        self.mouse_sprites = mouse_sprites
        self.dog_sprites = dog_sprites
        self.font = font
        self.bark_sound = bark_sound
        self.bell_sound = bell_sound
        self.victory_sound = victory_sound


TILE_WIDTH = 32
TILE_HEIGHT = 32

CHARACTER_WIDTH = 32
CHARACTER_HEIGHT = 32

CANVAS_WIDTH = 640
CANVAS_HEIGHT = 480


def load_media() -> Media:
    """Load the media from the file system."""
    return Media(
        cat_sprites={
            direction: [
                pygame.image.load(
                    str(
                        PACKAGE_DIR
                        / f"media/images/cat_{direction.name.lower()}{i}.png"
                    )
                ).convert_alpha()
                for i in range(3)
            ]
            for direction in Direction
        },
        mouse_sprites={
            direction: [
                pygame.image.load(
                    str(
                        PACKAGE_DIR
                        / f"media/images/mouse_{direction.name.lower()}{i}.png"
                    )
                ).convert_alpha()
                for i in range(3)
            ]
            for direction in Direction
        },
        dog_sprites={
            direction: [
                pygame.image.load(
                    str(
                        PACKAGE_DIR
                        / f"media/images/dog_{direction.name.lower()}{i}.png"
                    )
                ).convert_alpha()
                for i in range(3)
            ]
            for direction in Direction
        },
        # fmt: off
        font=pygame.freetype.Font(  # type: ignore
            str(PACKAGE_DIR / "media/fonts/freesansbold.ttf")
        ),
        # fmt: on
        bark_sound=pygame.mixer.Sound(str(PACKAGE_DIR / "media/sfx/bark.ogg")),
        bell_sound=pygame.mixer.Sound(str(PACKAGE_DIR / "media/sfx/bell.ogg")),
        victory_sound=pygame.mixer.Sound(str(PACKAGE_DIR / "media/sfx/victory.ogg")),
    )


#: Level width, in tiles
LEVEL_WIDTH = 20

#: Level height, in tiles
LEVEL_HEIGHT = 14


class InitialMap:
    """Capture the initial level map."""

    # fmt: on
    @require(lambda data: len(data) == LEVEL_HEIGHT)
    @require(lambda data: all(len(row) == LEVEL_WIDTH for row in data))
    @require(
        lambda data: sum(1 for row in data for character in row if character == "c")
        == 1,
        "Exactly one cat expected",
    )
    # fmt: off
    def __new__(cls, data: Sequence[str]) -> "InitialMap":
        return cast(InitialMap, data)

    def __getitem__(self, index: int) -> str:
        raise NotImplementedError("Only for type annotation.")

    def __len__(self) -> int:
        raise NotImplementedError("Only for type annotation.")

    def __iter__(self) -> Iterator[str]:
        raise NotImplementedError("Only for type annotation.")


# noinspection SpellCheckingInspection
INITIAL_MAP = InitialMap(
    [
        "##..#########...####",
        "#......m...........#",
        "#....##...##...#..##",
        "#...#########.......",
        "#....##.m......#...#",
        "#..d........#..#...#",
        "#...####...###......",
        "#...###.......#.#..#",
        "#.......#.....m....#",
        "....m...##..........",
        ".......###....###..#",
        "#.....##...##.......",
        "#........c.........#",
        "###.####...###.#####",
    ]
)


class Walking:
    """Capture the walking of an actor."""

    #: Start time, in seconds
    start: float

    #: Estimate time of arrival, in seconds
    eta: float

    #: Origin position as (x pixel, y pixel)
    origin_xy: Tuple[float, float]

    #: Target position as (x pixel, y pixel)
    target_xy: Tuple[float, float]

    def __init__(
        self,
        start: float,
        eta: float,
        origin_xy: Tuple[float, float],
        target_xy: Tuple[float, float],
    ) -> None:
        """Initialize with the given values."""
        self.start = start
        self.eta = eta
        self.origin_xy = origin_xy
        self.target_xy = target_xy


class Character(DBC):
    """Model a character in the game."""

    #: Position in the world, (x pixel, y pixel)
    xy: Tuple[float, float]

    #: Ongoing walk action, if any
    walking: Optional[Walking]

    #: Direction of the actor, when in the position
    direction: Direction

    def __init__(
        self, xy: Tuple[float, float], walking: Optional[Walking], direction: Direction
    ) -> None:
        """Initialize with the given values."""
        self.xy = xy
        self.walking = walking
        self.direction = direction

    @abc.abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError()


class Cat(Character):
    """Model the cat-player in the game."""

    #: Instruction to walk in the given direction at the next tick, if any
    direction_to_walk: Optional[Direction]

    def __init__(
        self,
        xy: Tuple[float, float],
        walking: Optional[Walking],
        direction: Direction,
        direction_to_walk: Optional[Direction],
    ) -> None:
        """Initialize with the given values."""
        Character.__init__(self, xy, walking, direction)
        self.direction_to_walk = direction_to_walk

    def __str__(self) -> str:
        return self.__class__.__name__


class NonPlayerCharacter(Character):
    """Model the non-player character in the game."""

    #: When to perform the next walk, in seconds
    next_walk: float

    def __init__(
        self,
        xy: Tuple[float, float],
        walking: Optional[Walking],
        direction: Direction,
        next_walk: float,
    ) -> None:
        """Initialize with the given values."""
        Character.__init__(self, xy, walking, direction)
        self.next_walk = next_walk


class Mouse(NonPlayerCharacter):
    """Represent a wandering mouse to be caught."""

    def __str__(self) -> str:
        return self.__class__.__name__


class Dog(NonPlayerCharacter):
    """Represent a cat-hunting dog."""

    def __str__(self) -> str:
        return self.__class__.__name__


class Tile(DBC):
    """Represent an abstract tile in a level."""

    #: Top-left corner, in (x pixel, y pixel)
    xy: Tuple[float, float]

    def __init__(self, xy: Tuple[float, float]) -> None:
        """Initialize with the given values."""
        self.xy = xy

    @abc.abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError()


class Block(Tile):
    """Represent a blocking tile in a level."""

    def __init__(self, xy: Tuple[float, float]) -> None:
        """Initialize with the given values."""
        Tile.__init__(self, xy)

    def __str__(self) -> str:
        return self.__class__.__name__


class Floor(Tile):
    """Represent a non-blocking tile in a level."""

    def __init__(self, xy: Tuple[float, float]) -> None:
        """Initialize with the given values."""
        Tile.__init__(self, xy)

    def __str__(self) -> str:
        return self.__class__.__name__


TileUnion = Union[Block, Floor]


class State:
    """Capture the global state of the game."""

    #: Set if we received the signal to quit the game
    received_quit: bool

    #: Timestamp when the game started, in seconds since epoch
    game_start: float

    #: Current clock in the game, in seconds since epoch
    now: float

    #: Set when the game finishes
    game_over: Optional[dancecattomouse.events.GameOverKind]

    #: Time of the game over, in seconds since epoch
    game_end: Optional[float]

    level: Sequence[Sequence[TileUnion]]

    cat: Cat

    mice: List[Mouse]

    dogs: List[Dog]

    def __init__(self, game_start: float, initial_map: InitialMap) -> None:
        """Initialize with the given values and the defaults."""
        initialize_state(self, game_start, initial_map)


def initialize_state(state: State, game_start: float, initial_map: InitialMap) -> None:
    """Initialize the state to the start one."""
    state.received_quit = False
    state.game_start = game_start
    state.now = game_start
    state.game_over = None
    state.game_end = None

    state.mice = []
    state.dogs = []

    level = []  # type: List[List[TileUnion]]

    directions = [  # pylint: disable=unnecessary-comprehension
        direction for direction in Direction
    ]

    for row_i, initial_map_row in enumerate(initial_map):
        tile_row = []  # type: List[TileUnion]

        for column_i, initial_map_cell in enumerate(initial_map_row):
            xy = (column_i * TILE_WIDTH, row_i * TILE_HEIGHT)

            if initial_map_cell == "#":
                tile_row.append(Block(xy))
            elif initial_map_cell == ".":
                tile_row.append(Floor(xy))
            elif initial_map_cell == "c":
                state.cat = Cat(
                    xy=xy,
                    walking=None,
                    direction=random.choice(directions),
                    direction_to_walk=None,
                )

                tile_row.append(Floor(xy))
            elif initial_map_cell == "d":
                dog = Dog(
                    xy=xy,
                    walking=None,
                    direction=random.choice(directions),
                    next_walk=state.game_start + random.random() * 3,
                )

                state.dogs.append(dog)
                tile_row.append(Floor(xy))
            elif initial_map_cell == "m":
                mouse = Mouse(
                    xy=(column_i * TILE_WIDTH, row_i * TILE_HEIGHT),
                    walking=None,
                    direction=random.choice(directions),
                    next_walk=state.game_start + random.random() * 3,
                )

                state.mice.append(mouse)
                tile_row.append(Floor(xy))
            else:
                raise ValueError(
                    f"Unknown cell in the initial map: {repr(initial_map_cell)}"
                )

        level.append(tile_row)

    state.level = level


@require(lambda xmin_a, xmax_a: xmin_a <= xmax_a)
@require(lambda ymin_a, ymax_a: ymin_a <= ymax_a)
@require(lambda xmin_b, xmax_b: xmin_b <= xmax_b)
@require(lambda ymin_b, ymax_b: ymin_b <= ymax_b)
def intersect(
    xmin_a: Union[int, float],
    ymin_a: Union[int, float],
    xmax_a: Union[int, float],
    ymax_a: Union[int, float],
    xmin_b: Union[int, float],
    ymin_b: Union[int, float],
    xmax_b: Union[int, float],
    ymax_b: Union[int, float],
) -> bool:
    """Return true if the two bounding boxes intersect."""
    return (xmin_a <= xmax_b and xmax_a >= xmin_b) and (
        ymin_a <= ymax_b and ymax_a >= ymin_b
    )


#: Walk duration of all characters, in seconds
WALK_DURATION = 0.25


def xy_to_row_column(xy: Tuple[float, float]) -> Tuple[int, int]:
    """Convert the (x pixel, y pixel) position to a (row, column) tile index."""
    row_i = int(xy[1] / TILE_WIDTH)
    column_i = int(xy[0] / TILE_HEIGHT)

    return row_i, column_i


def row_column_to_xy(row_column: Tuple[int, int]) -> Tuple[float, float]:
    """Convert the (i row, j column) tile position to a (x pixel, y pixel) position."""
    return float(row_column[1] * TILE_WIDTH), float(row_column[0] * TILE_HEIGHT)


def compute_next_row_column(
    row_column: Tuple[int, int], direction: Direction
) -> Tuple[int, int]:
    """Compute the (row, column) tile index from ``row_column`` in ``direction``."""
    if direction is Direction.NORTH:
        return row_column[0] - 1, row_column[1]
    elif direction is Direction.EAST:
        return row_column[0], row_column[1] + 1
    elif direction is Direction.SOUTH:
        return row_column[0] + 1, row_column[1]
    elif direction is Direction.WEST:
        return row_column[0], row_column[1] - 1
    else:
        assert_never(direction)


def over_neighbour_row_column(row_column: Tuple[int, int]) -> Iterator[Tuple[int, int]]:
    """Iterate over the neighbouring tiles."""
    for direction in Direction:
        yield compute_next_row_column(row_column, direction)


def direction_from_walking(walking: Walking) -> Direction:
    """
    Compute the direction based on the walk vector.
    """
    x_delta = walking.target_xy[0] - walking.origin_xy[0]
    y_delta = walking.target_xy[1] - walking.origin_xy[1]

    if abs(x_delta) < abs(y_delta):
        if y_delta > 0:
            result = Direction.SOUTH
        else:
            result = Direction.NORTH
    else:
        if x_delta > 0:
            result = Direction.EAST
        else:
            result = Direction.WEST

    return result


BUTTON_TO_DIRECTION = {
    dancecattomouse.events.Button.UP: Direction.NORTH,
    dancecattomouse.events.Button.LEFT: Direction.WEST,
    dancecattomouse.events.Button.DOWN: Direction.SOUTH,
    dancecattomouse.events.Button.RIGHT: Direction.EAST,
}


def handle_in_game(
    state: State, our_event_queue: List[dancecattomouse.events.Event], media: Media
) -> None:
    """Consume the first action in the queue during the game."""
    if len(our_event_queue) == 0:
        return

    event = our_event_queue.pop(0)

    now = pygame.time.get_ticks() / 1000

    if isinstance(event, dancecattomouse.events.Tick):
        state.now = now

        # If we ate all the mice, we are done with the game.
        if len(state.mice) == 0:
            our_event_queue.append(
                dancecattomouse.events.GameOver(
                    kind=dancecattomouse.events.GameOverKind.MICE_EATEN
                )
            )

        # Check that no cat has been eaten
        for dog in state.dogs:
            if intersect(
                dog.xy[0],
                dog.xy[1],
                dog.xy[0] + CHARACTER_WIDTH - 1,
                dog.xy[1] + CHARACTER_HEIGHT - 1,
                state.cat.xy[0],
                state.cat.xy[1],
                state.cat.xy[0] + CHARACTER_WIDTH - 1,
                state.cat.xy[1] + CHARACTER_HEIGHT - 1,
            ):
                our_event_queue.append(
                    dancecattomouse.events.GameOver(
                        kind=dancecattomouse.events.GameOverKind.DOG
                    )
                )
                return

        # Eat all the mice
        updated_mice = []  # type: List[Mouse]
        for mouse in state.mice:
            if intersect(
                mouse.xy[0],
                mouse.xy[1],
                mouse.xy[0] + CHARACTER_WIDTH - 1,
                mouse.xy[1] + CHARACTER_HEIGHT - 1,
                state.cat.xy[0],
                state.cat.xy[1],
                state.cat.xy[0] + CHARACTER_WIDTH - 1,
                state.cat.xy[1] + CHARACTER_HEIGHT - 1,
            ):
                media.bell_sound.play()
                continue

            updated_mice.append(mouse)

        state.mice = updated_mice

        # Reconstruct the occupied tiles
        occupied = set()  # type: Set[Tuple[int, int]]

        for row_i, tile_row in enumerate(state.level):
            for column_i, tile in enumerate(tile_row):
                if isinstance(tile, Block):
                    occupied.add((row_i, column_i))

        for character in itertools.chain([state.cat], state.dogs, state.mice):
            if character.walking is None:
                occupied.add(xy_to_row_column(character.xy))
            else:
                occupied.add(xy_to_row_column(character.walking.target_xy))

        # Walk the non-player characters, if it's due
        for npc in itertools.chain(state.dogs, state.mice):
            if npc.walking is None and now > npc.next_walk:
                row_column = xy_to_row_column(npc.xy)

                next_rows_columns = [
                    next_row_column
                    for next_row_column in over_neighbour_row_column(row_column)
                    if (
                        next_row_column not in occupied
                        and 0 <= next_row_column[0] < LEVEL_HEIGHT
                        and 0 <= next_row_column[1] < LEVEL_WIDTH
                    )
                ]

                if len(next_rows_columns) > 0:
                    next_row_column = random.choice(next_rows_columns)

                    npc.walking = Walking(
                        start=now,
                        eta=now + WALK_DURATION,
                        origin_xy=npc.xy,
                        target_xy=row_column_to_xy(next_row_column),
                    )

                    occupied.remove(row_column)
                    occupied.add(next_row_column)

                    npc.next_walk = now + 3 + random.random() * 5

        # Walk the cat, if it's due
        if state.cat.direction_to_walk is not None:
            assert (
                state.cat.walking is None
            ), "Cat can not be walking and instructed to walk"

            row_column = xy_to_row_column(state.cat.xy)
            target_row_column = compute_next_row_column(
                row_column, state.cat.direction_to_walk
            )

            target_tile = (
                state.level[target_row_column[0]][target_row_column[1]]
                if (
                    0 <= target_row_column[0] < LEVEL_HEIGHT
                    and 0 <= target_row_column[1] < LEVEL_WIDTH
                )
                else None
            )

            if target_tile is None or isinstance(target_tile, Block):
                # We can not walk into the block or out of the map, but we change
                # the direction.
                state.cat.direction = state.cat.direction_to_walk
            elif isinstance(target_tile, Floor):
                state.cat.walking = Walking(
                    start=now,
                    eta=now + WALK_DURATION,
                    origin_xy=state.cat.xy,
                    target_xy=row_column_to_xy(target_row_column),
                )

                occupied.remove(row_column)
                occupied.add(target_row_column)
            else:
                raise AssertionError(f"Unexpected type of floor: {type(target_tile)}")

            state.cat.direction_to_walk = None

        # Execute all the walks
        for character in itertools.chain([state.cat], state.dogs, state.mice):
            if character.walking is not None:
                if now < character.walking.start:
                    pass
                elif now < character.walking.eta:
                    x_delta = (
                        character.walking.target_xy[0] - character.walking.origin_xy[0]
                    )
                    y_delta = (
                        character.walking.target_xy[1] - character.walking.origin_xy[1]
                    )

                    fraction = (now - character.walking.start) / (
                        character.walking.eta - character.walking.start
                    )

                    xy = (
                        character.walking.origin_xy[0] + x_delta * fraction,
                        character.walking.origin_xy[1] + y_delta * fraction,
                    )

                    character.xy = xy
                else:
                    # The walk is over.
                    character.xy = character.walking.target_xy
                    character.direction = direction_from_walking(character.walking)
                    character.walking = None

    elif isinstance(event, dancecattomouse.events.ButtonDown):
        if state.cat.walking is None:
            direction = BUTTON_TO_DIRECTION.get(event.button, None)
            if direction is not None:
                state.cat.direction_to_walk = direction
    else:
        # Ignore the event
        pass


def handle(
    state: State,
    our_event_queue: List[dancecattomouse.events.Event],
    clock: pygame.time.Clock,
    media: Media,
) -> None:
    """Consume the first action in the queue."""
    if len(our_event_queue) == 0:
        return

    if isinstance(our_event_queue[0], dancecattomouse.events.ReceivedQuit):
        our_event_queue.pop(0)
        state.received_quit = True

    elif isinstance(our_event_queue[0], dancecattomouse.events.ReceivedRestart):
        our_event_queue.pop(0)
        pygame.mixer.stop()
        initialize_state(
            state, game_start=pygame.time.get_ticks() / 1000, initial_map=INITIAL_MAP
        )

    elif isinstance(our_event_queue[0], dancecattomouse.events.GameOver):
        event = our_event_queue[0]
        our_event_queue.pop(0)

        if state.game_over is None:
            state.game_over = event.kind
            state.game_end = pygame.time.get_ticks() / 1000

            if state.game_over is dancecattomouse.events.GameOverKind.MICE_EATEN:
                media.victory_sound.play()
            elif state.game_over is dancecattomouse.events.GameOverKind.DOG:
                media.bark_sound.play()
                pass
            else:
                assert_never(state.game_over)
    else:
        handle_in_game(state, our_event_queue, media)


def render_game_over(state: State, media: Media) -> pygame.surface.Surface:
    """Render the "game over" dialogue as a scene."""
    scene = pygame.surface.Surface((CANVAS_WIDTH, CANVAS_HEIGHT))
    scene.fill((0, 0, 0))

    assert state.game_over is not None

    if state.game_over is dancecattomouse.events.GameOverKind.MICE_EATEN:
        assert state.game_end is not None

        game_duration = state.game_end - state.game_start
        minutes = int(game_duration / 60)
        seconds = int(game_duration - minutes * 60)

        media.font.render_to(
            scene,
            (20, 20),
            f"Bravo! Your time: {minutes:02d}:{seconds:02d}",
            (255, 255, 255),
            size=16,
        )
    elif state.game_over is dancecattomouse.events.GameOverKind.DOG:
        media.font.render_to(scene, (20, 20), "Game Over :'(", (255, 255, 255), size=16)

    else:
        assert_never(state.game_over)

    media.font.render_to(
        scene,
        (20, CANVAS_HEIGHT - 20),
        'Press "q" to quit and "r" to restart',
        (255, 255, 255),
        size=16,
    )

    return scene


def render_quit(media: Media) -> pygame.surface.Surface:
    """Render the "Quitting..." dialogue as a scene."""
    scene = pygame.surface.Surface((CANVAS_WIDTH, CANVAS_HEIGHT))
    scene.fill((0, 0, 0))

    media.font.render_to(scene, (20, 20), "Quitting...", (255, 255, 255), size=32)

    return scene


def render_game(state: State, media: Media) -> pygame.surface.Surface:
    """Render the game scene."""
    canvas = pygame.surface.Surface(
        (TILE_WIDTH * LEVEL_WIDTH, TILE_HEIGHT * (LEVEL_HEIGHT + 1))
    )
    canvas.fill((0, 0, 0))

    game_duration = state.now - state.game_start
    minutes = int(game_duration / 60)
    seconds = int(game_duration - minutes * 60)

    media.font.render_to(
        canvas, (10, 2), f"Time: {minutes:02d}:{seconds:02d}", (255, 255, 255), size=15
    )

    scene_start = (0, TILE_HEIGHT / 2)

    for row_i, row in enumerate(state.level):
        for column_i, tile in enumerate(row):
            color = None  # type: Optional[Tuple[int, int, int]]
            if isinstance(tile, Block):
                color = (0, 0, 0)
            elif isinstance(tile, Floor):
                color = (242, 209, 107)
            else:
                assert_never(tile)

            assert color is not None

            pygame.draw.rect(
                canvas,
                color,
                pygame.Rect(
                    (
                        scene_start[0] + column_i * TILE_WIDTH,
                        scene_start[1] + row_i * TILE_HEIGHT,
                        TILE_WIDTH,
                        TILE_HEIGHT,
                    )
                ),
            )

    for character in itertools.chain([state.cat], state.dogs, state.mice):
        assert isinstance(character, (Cat, Dog, Mouse))

        sprite_map: Optional[
            Mapping[Direction, Sequence[pygame.surface.Surface]]
        ] = None

        if isinstance(character, Cat):
            sprite_map = media.cat_sprites
        elif isinstance(character, Dog):
            sprite_map = media.dog_sprites
        elif isinstance(character, Mouse):
            sprite_map = media.mouse_sprites
        else:
            assert_never(character)

        if character.walking is None:
            sprite = sprite_map[character.direction][0]
        else:
            fraction = (state.now - character.walking.start) / (
                character.walking.eta - character.walking.start
            )

            sprite_sequence = sprite_map[direction_from_walking(character.walking)]

            # fmt: off
            sprite_index = max(
                0,
                min(
                    len(sprite_sequence) - 1,
                    int(fraction * len(sprite_sequence))
                )
            )
            # fmt: on

            sprite = sprite_sequence[sprite_index]

        canvas.blit(
            sprite,
            (
                int(scene_start[0] + character.xy[0]),
                int(scene_start[1] + character.xy[1]),
            ),
        )

    media.font.render_to(
        canvas,
        (10, CANVAS_HEIGHT - TILE_HEIGHT / 2),
        'Press "q" to quit and "r" to restart',
        (255, 255, 255),
        size=10,
    )

    return canvas


def render(state: State, media: Media) -> pygame.surface.Surface:
    """Render the state of the program."""
    if state.received_quit:
        return render_quit(media)

    if state.game_over is not None:
        return render_game_over(state, media)

    return render_game(state, media)


def resize_scene_to_surface_and_blit(
    scene: pygame.surface.Surface, surface: pygame.surface.Surface
) -> None:
    """Draw the scene on surface resizing it to maximum at constant aspect ratio."""
    surface.fill((0, 0, 0))

    surface_aspect_ratio = fractions.Fraction(surface.get_width(), surface.get_height())
    scene_aspect_ratio = fractions.Fraction(scene.get_width(), scene.get_height())

    if scene_aspect_ratio < surface_aspect_ratio:
        new_scene_height = surface.get_height()
        new_scene_width = scene.get_width() * (new_scene_height / scene.get_height())

        scene = pygame.transform.scale(scene, (new_scene_width, new_scene_height))

        margin = int((surface.get_width() - scene.get_width()) / 2)

        surface.blit(scene, (margin, 0))

    elif scene_aspect_ratio == surface_aspect_ratio:
        new_scene_width = surface.get_width()
        new_scene_height = scene.get_height()

        scene = pygame.transform.scale(scene, (new_scene_width, new_scene_height))

        surface.blit(scene, (0, 0))
    else:
        new_scene_width = surface.get_width()
        new_scene_height = int(
            scene.get_height() * (new_scene_width / scene.get_width())
        )

        scene = pygame.transform.scale(scene, (new_scene_width, new_scene_height))

        margin = int((surface.get_height() - scene.get_height()) / 2)

        surface.blit(scene, (0, margin))


def main(prog: str) -> int:
    """
    Execute the main routine.

    :param prog: name of the program to be displayed in the help
    :return: exit code
    """
    pygame.joystick.init()
    joysticks = [
        pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())
    ]

    parser = argparse.ArgumentParser(prog=prog, description=__doc__)
    parser.add_argument(
        "--version", help="show the current version and exit", action="store_true"
    )

    parser.add_argument(
        "--list_joysticks", help="List joystick GUIDs and exit", action="store_true"
    )
    if len(joysticks) >= 1:
        parser.add_argument(
            "--joystick",
            help="Joystick to use for the game",
            choices=[joystick.get_guid() for joystick in joysticks],
            default=joysticks[0].get_guid(),
        )

    # The module ``argparse`` is not flexible enough to understand special options such
    # as ``--version`` so we manually hard-wire.
    if "--version" in sys.argv and "--help" not in sys.argv:
        print(dancecattomouse.__version__)
        return 0

    if "--list_joysticks" in sys.argv and "--help" not in sys.argv:
        for joystick in joysticks:
            print(f"Joystick {joystick.get_name()}, GUID: {joystick.get_guid()}")
        return 0

    args = parser.parse_args()

    # noinspection PyUnusedLocal
    active_joystick = None  # type: Optional[pygame.joystick.Joystick]

    if len(joysticks) == 0:
        print(
            f"There are no joysticks plugged in. "
            f"{prog.capitalize()} requires a joystick.",
            file=sys.stderr,
        )
        return 1

    else:
        active_joystick = next(
            joystick for joystick in joysticks if joystick.get_guid() == args.joystick
        )

    assert active_joystick is not None
    print(
        f"Using the joystick: {active_joystick.get_name()} {active_joystick.get_guid()}"
    )

    # NOTE (mristin, 2023-01-08):
    # We have to think a bit better about how to deal with keyboard and joystick input.
    # For rapid development, we simply map the buttons of our concrete dance mat to
    # button numbers.
    button_map = {
        6: dancecattomouse.events.Button.CROSS,
        2: dancecattomouse.events.Button.UP,
        7: dancecattomouse.events.Button.CIRCLE,
        3: dancecattomouse.events.Button.RIGHT,
        5: dancecattomouse.events.Button.SQUARE,
        1: dancecattomouse.events.Button.DOWN,
        4: dancecattomouse.events.Button.TRIANGLE,
        0: dancecattomouse.events.Button.LEFT,
    }

    pygame.init()
    pygame.mixer.pre_init()
    pygame.mixer.init()

    pygame.display.set_caption("dance-cat-to-mouse")
    surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    try:
        media = load_media()
    except Exception as exception:
        print(
            f"Failed to load the media: {exception.__class__.__name__} {exception}",
            file=sys.stderr,
        )
        return 1

    now = pygame.time.get_ticks() / 1000
    clock = pygame.time.Clock()

    state = State(game_start=now, initial_map=INITIAL_MAP)

    our_event_queue = []  # type: List[dancecattomouse.events.Event]

    # Reuse the tick object so that we don't have to create it every time
    tick_event = dancecattomouse.events.Tick()

    allow_arrow_keys = False
    arrow_key_to_button = {
        pygame.K_DOWN: dancecattomouse.events.Button.DOWN,
        pygame.K_UP: dancecattomouse.events.Button.UP,
        pygame.K_LEFT: dancecattomouse.events.Button.LEFT,
        pygame.K_RIGHT: dancecattomouse.events.Button.RIGHT,
    }

    try:
        while not state.received_quit:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    our_event_queue.append(dancecattomouse.events.ReceivedQuit())

                elif (
                    event.type == pygame.JOYBUTTONDOWN
                    and joysticks[event.instance_id] is active_joystick
                ):
                    # NOTE (mristin, 2023-01-08):
                    # Map joystick buttons to our canonical buttons;
                    # This is necessary if we ever want to support other dance mats.
                    our_button = button_map.get(event.button, None)
                    if our_button is not None:
                        our_event_queue.append(
                            dancecattomouse.events.ButtonDown(our_button)
                        )

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        our_event_queue.append(dancecattomouse.events.ReceivedQuit())
                    elif event.key == pygame.K_r:
                        # NOTE (mristin, 2023-01-08):
                        # Restart the game whenever "r" is pressed
                        our_event_queue.append(dancecattomouse.events.ReceivedRestart())
                    else:
                        # NOTE (mristin, 2023-01-08):
                        # The following keys are only handled for debugging / demos.
                        if allow_arrow_keys:
                            button = arrow_key_to_button.get(event.key, None)
                            if button is not None:
                                our_event_queue.append(
                                    dancecattomouse.events.ButtonDown(button)
                                )
                        else:
                            pass

                else:
                    # Ignore the event that we do not handle
                    pass

            our_event_queue.append(tick_event)

            while len(our_event_queue) > 0:
                handle(state, our_event_queue, clock, media)

            scene = render(state, media)
            resize_scene_to_surface_and_blit(scene, surface)
            pygame.display.flip()

            # Enforce 30 frames per second
            clock.tick(30)

    finally:
        print("Quitting the game...")
        tic = time.time()
        pygame.joystick.quit()
        pygame.quit()
        print(f"Quit the game after: {time.time() - tic:.2f} seconds")

    return 0


def entry_point() -> int:
    """Provide an entry point for a console script."""
    return main(prog="dance-cat-to-mouse")


if __name__ == "__main__":
    sys.exit(main(prog="dance-cat-to-mouse"))
