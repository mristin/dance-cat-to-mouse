"""Generate all the files for the game project using a dance mat."""

import argparse
import os
import pathlib
import sys


def write_or_raise_if_exists(path: pathlib.Path, text: str) -> None:
    """Write the ``text`` to ``path`` or raise if ``path`` exists."""
    if path.exists():
        raise FileExistsError(f"The file has been already generated: {path}")

    path.write_text(text, encoding='utf-8')


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.parse_args()

    this_path = pathlib.Path(os.path.realpath(__file__))
    repo_root = this_path.parent.parent

    description = (
        """\
Dance collaboratively the cat to catch the mouse."""
    )

    command = "dance-cat-to-mouse"
    module_name = "dancecattomouse"

    repo_url = f"https://github.com/mristin/{command}"
    media_url = f"https://media.githubusercontent.com/media/mristin/dance-a-mole-desktop/main"

    keywords = "dance pad cat mouse catch"

    today = "2023-01-08"

    # All variables are set from here on.

    write_or_raise_if_exists(
        (repo_root / "requirements.txt"),
        """\
icontract>=2.6.1,<3
pygame>=2,<3
"""
    )

    write_or_raise_if_exists(
        repo_root / "setup.py",
        f'''\
"""
A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

import os
import sys

from setuptools import setup, find_packages

# pylint: disable=redefined-builtin

here = os.path.abspath(os.path.dirname(__file__))  # pylint: disable=invalid-name

with open(os.path.join(here, "README.rst"), encoding="utf-8") as fid:
    long_description = fid.read()  # pylint: disable=invalid-name

with open(os.path.join(here, "requirements.txt"), encoding="utf-8") as fid:
    install_requires = [line for line in fid.read().splitlines() if line.strip()]

setup(
    name={repr(command)},
    # Don't forget to update the version in __init__.py and CHANGELOG.rst!
    version="0.0.1",
    description={repr(description)},
    long_description=long_description,
    url={repr(repo_url)},
    author="Marko Ristin",
    author_email="marko@ristin.ch",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Education',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.9'
    ],
    license="License :: OSI Approved :: MIT License",
    keywords={repr(keywords)},
    install_requires=install_requires,
    extras_require={{
        "dev": [
            "black==22.12.0",
            "mypy==0.991",
            "pylint==2.15.8",
            "coverage>=6.5.0,<7",
            "twine",
            "pyinstaller>=5,<6",
            "pillow>=9,<10",
            "requests>=2,<3",
        ],
    }},
    py_modules=[{repr(module_name)}],
    packages=find_packages(exclude=["tests", "continuous_integration", "dev_scripts"]),
    package_data={{
        {repr(module_name)}: [
            "media/images/*",
            "media/sfx/*",
        ]
    }},
    data_files=[
        (".", ["LICENSE", "README.rst", "requirements.txt"]),
    ],
    entry_points={{
        "console_scripts": [
            "{command}={module_name}.main:entry_point",
        ]
    }},
)
'''
    )

    title_line = "*" * len(command)

    write_or_raise_if_exists(
        repo_root / "README.rst",
        f"""\
{title_line}
{command}
{title_line}

{description}

.. image:: {repo_url}/actions/workflows/ci.yml/badge.svg
    :target: {repo_url}/actions/workflows/ci.yml
    :alt: Continuous integration

.. image:: {media_url}/screenshot.png
    :alt: Screenshot

Installation
============
Download and unzip a version of the game from the `Releases`_.

.. _Releases: {repo_url}/releases

Running
=======
You need to connect the dance mat *before* starting the game.

Run ``{command}.exe`` (in the directory where you unzipped the game).

If you have multiple joysticks attached, the first joystick is automatically selected, and assumed to be the dance mat.

If the first joystick does not correspond to your dance mat, list the available joysticks with the following command in the command prompt:

.. code-block::

    {command}.exe --list_joysticks

You will see the names and unique IDs (GUIDs) of your joysticks.
Select the joystick that you wish by providing its GUI.
For example:

.. code-block::

    {command}.exe -joystick 03000000790000001100000000000000

Which dance mat to use?
=======================
We used an unbranded dance mat which you can order, say, from Amazon:
https://www.amazon.com/OSTENT-Non-Slip-Dancing-Dance-Compatible-PC/dp/B00FJ2KT8M

Please let us know by `creating an issue`_ if you tested the game with other mats!

.. _creating an issue: {repo_url}/issues/new

Acknowledgments
===============
"""
    )

    module_dir = repo_root / module_name
    module_dir.mkdir(exist_ok=True)

    (module_dir / "media/sfx").mkdir(exist_ok=True, parents=True)
    (module_dir / "media/images").mkdir(exist_ok=True, parents=True)
    (module_dir / "media/fonts").mkdir(exist_ok=True, parents=True)

    write_or_raise_if_exists(
        module_dir / "__init__.py",
        f"""\
\"\"\"{description}\"\"\"

__version__ = "0.0.1"
__author__ = "Marko Ristin"
__license__ = "License :: OSI Approved :: MIT License"
__status__ = "Production/Stable"
"""
    )

    write_or_raise_if_exists(
        module_dir / "main.py",
        f'''\
"""{description}"""

import argparse
import fractions
import importlib.resources
import os.path
import pathlib
import random
import sys
import time
from typing import Optional, Final, List, MutableMapping, Union, Tuple

import pygame
import pygame.freetype
from icontract import require, snapshot, ensure

import {module_name}
import {module_name}.events
from {module_name}.common import assert_never

assert {module_name}.__doc__ == __doc__

PACKAGE_DIR = (
    pathlib.Path(str(importlib.resources.files(__package__)))
    if __package__ is not None
    else pathlib.Path(os.path.realpath(__file__)).parent
)


class Media:
    """Represent all the media loaded in the main memory from the file system."""

    def __init__(
        self,
        font: pygame.freetype.Font,  # type: ignore
    ) -> None:
        """Initialize with the given values."""
        self.font = font

# TODO: adapt to the game
SCENE_WIDTH = 640
SCENE_HEIGHT = 480

def load_media() -> Media:
    """Load the media from the file system."""
    return Media(
        # fmt: off
        font=pygame.freetype.Font(  # type: ignore
            str(PACKAGE_DIR / "media/fonts/freesansbold.ttf")
        ),
        # fmt: on
    )


class State:
    """Capture the global state of the game."""

    #: Set if we received the signal to quit the game
    received_quit: bool

    #: Timestamp when the game started, seconds since epoch
    game_start: float

    #: Current clock in the game, seconds since epoch
    now: float

    #: Set when the game finishes
    game_over: Optional[{module_name}.events.GameOverKind]

    def __init__(self, game_start: float) -> None:
        """Initialize with the given values and the defaults."""
        initialize_state(self, game_start)


def initialize_state(state: State, game_start: float) -> None:
    """Initialize the state to the start one."""
    state.received_quit = False
    state.game_start = game_start
    state.now = game_start
    state.game_over = None


def handle_in_game(
    state: State,
    our_event_queue: List[{module_name}.events.EventUnion],
    media: Media
) -> None:
    """Consume the first action in the queue during the game."""
    if len(our_event_queue) == 0:
        return

    event = our_event_queue.pop(0)

    now = pygame.time.get_ticks() / 1000

    if isinstance(event, {module_name}.events.Tick):
        time_delta = now - state.now

        state.now = now
    # TODO: handle other types of events
    else:
        # Ignore the event
        pass


def handle(
    state: State,
    our_event_queue: List[{module_name}.events.EventUnion],
    clock: pygame.time.Clock,
    media: Media
) -> None:
    """Consume the first action in the queue."""
    if len(our_event_queue) == 0:
        return

    if isinstance(our_event_queue[0], {module_name}.events.ReceivedQuit):
        our_event_queue.pop(0)
        state.received_quit = True

    elif isinstance(our_event_queue[0], {module_name}.events.ReceivedRestart):
        our_event_queue.pop(0)
        initialize_state(state, game_start=pygame.time.get_ticks() / 1000)

    elif isinstance(our_event_queue[0], {module_name}.events.GameOver):
        event = our_event_queue[0]
        our_event_queue.pop(0)

        if state.game_over is None:
            state.game_over = event.kind
            if state.game_over is {module_name}.events.GameOverKind.HAPPY_END:
                # TODO: implement
                raise NotImplementedError()
            # TODO: handle other kinds of game over
            else:
                assert_never(state.game_over)
    else:
        handle_in_game(state, our_event_queue, media)


def render_game_over(state: State, media: Media) -> pygame.surface.Surface:
    """Render the "game over" dialogue as a scene."""
    scene = pygame.surface.Surface((SCENE_WIDTH, SCENE_HEIGHT))
    scene.fill((0, 0, 0))

    assert state.game_over is not None

    if state.game_over is {module_name}.events.GameOverKind.HAPPY_END:
        # TODO: implement
        raise NotImplementedError()
    else:
        assert_never(state.game_over)

    media.font.render_to(
        scene,
        (20, SCENE_HEIGHT - 20),
        'Press "q" to quit and "r" to restart',
        (255, 255, 255),
        size=16,
    )

    return scene


def render_quit(media: Media) -> pygame.surface.Surface:
    """Render the "Quitting..." dialogue as a scene."""
    scene = pygame.surface.Surface((SCENE_WIDTH, SCENE_HEIGHT))
    scene.fill((0, 0, 0))

    media.font.render_to(scene, (20, 20), "Quitting...", (255, 255, 255), size=32)

    return scene


def render_game(state: State, media: Media) -> pygame.surface.Surface:
    """Render the game scene."""
    # TODO: implement
    raise NotImplementedError()
    scene = media.background.copy()

    media.font.render_to(
        scene, (10, 490), 'Press "q" to quit and "r" to restart', (0, 0, 0), size=12
    )

    return scene


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
        print({module_name}.__version__)
        return 0

    if "--list_joysticks" in sys.argv and "--help" not in sys.argv:
        for joystick in joysticks:
            print(f"Joystick {{joystick.get_name()}}, GUID: {{joystick.get_guid()}}")
        return 0

    args = parser.parse_args()

    # noinspection PyUnusedLocal
    active_joystick = None  # type: Optional[pygame.joystick.Joystick]

    if len(joysticks) == 0:
        print(
            f"There are no joysticks plugged in. "
            f"{{prog.capitalize()}} requires a joystick.",
            file=sys.stderr,
        )
        return 1

    else:
        active_joystick = next(
            joystick for joystick in joysticks if joystick.get_guid() == args.joystick
        )

    assert active_joystick is not None
    print(
        f"Using the joystick: {{active_joystick.get_name()}} {{active_joystick.get_guid()}}"
    )

    # NOTE (mristin, {today}):
    # We have to think a bit better about how to deal with keyboard and joystick input.
    # For rapid development, we simply map the buttons of our concrete dance mat to
    # button numbers.
    button_map = {{
        6: {module_name}.events.Button.CROSS,
        2: {module_name}.events.Button.UP,
        7: {module_name}.events.Button.CIRCLE,
        3: {module_name}.events.Button.RIGHT,
        5: {module_name}.events.Button.SQUARE,
        1: {module_name}.events.Button.DOWN,
        4: {module_name}.events.Button.TRIANGLE,
        0: {module_name}.events.Button.LEFT,
    }}

    pygame.init()
    pygame.mixer.pre_init()
    pygame.mixer.init()

    pygame.display.set_caption({repr(command)})
    surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    try:
        media = load_media()
    except Exception as exception:
        print(
            f"Failed to load the media: {{exception.__class__.__name__}} {{exception}}",
            file=sys.stderr,
        )
        return 1

    now = pygame.time.get_ticks() / 1000
    clock = pygame.time.Clock()

    state = State(game_start=now)

    our_event_queue = []  # type: List[{module_name}.events.Event]

    # Reuse the tick object so that we don't have to create it every time
    tick_event = {module_name}.events.Tick()

    try:
        while not state.received_quit:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    our_event_queue.append({module_name}.events.ReceivedQuit())

                elif (
                    event.type == pygame.JOYBUTTONDOWN
                    and joysticks[event.instance_id] is active_joystick
                ):
                    # NOTE (mristin, {today}):
                    # Map joystick buttons to our canonical buttons;
                    # This is necessary if we ever want to support other dance mats.
                    our_button = button_map.get(event.button, None)
                    if our_button is not None:
                        our_event_queue.append({module_name}.events.ButtonDown(our_button))

                elif event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_ESCAPE,
                    pygame.K_q,
                ):
                    our_event_queue.append({module_name}.events.ReceivedQuit())

                elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    # NOTE (mristin, {today}):
                    # Restart the game whenever "r" is pressed
                    our_event_queue.append({module_name}.events.ReceivedRestart())

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
        print(f"Quit the game after: {{time.time() - tic:.2f}} seconds")

    return 0


def entry_point() -> int:
    """Provide an entry point for a console script."""
    return main(prog={repr(command)})


if __name__ == "__main__":
    sys.exit(main(prog={repr(command)}))
'''
    )

    write_or_raise_if_exists(
        module_dir / "events.py",
        f'''\
"""Define the game events."""

import abc
import enum
from typing import Union

from icontract import DBC


class Event(DBC):
    """Represent an abstract event in the game."""

    @abc.abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError()


class Tick(Event):
    """Mark a tick in the (irregular) game clock."""

    def __str__(self) -> str:
        return self.__class__.__name__


class ReceivedQuit(Event):
    """Signal that we have to exit the game."""

    def __str__(self) -> str:
        return self.__class__.__name__


class GameOverKind(enum.Enum):
    """Model different game endings."""

    HAPPY_END = 0
    # TODO: specify other kinds of game over


class GameOver(Event):
    """Signal that we have to exit the game."""

    def __init__(self, kind: GameOverKind) -> None:
        """Initialize with the given values."""
        self.kind = kind

    def __str__(self) -> str:
        return self.__class__.__name__


class Button(enum.Enum):
    """
    Represent abstract buttons, not necessarily tied to a concrete joystick.

    The enumeration of the buttons should follow the circle, with upper left being
    enumerated 0.
    """

    CROSS = 0
    UP = 1
    CIRCLE = 2
    RIGHT = 3
    SQUARE = 4
    DOWN = 5
    TRIANGLE = 6
    LEFT = 7


class ButtonDown(Event):
    """Capture the button down events."""

    def __init__(self, button: Button) -> None:
        """Initialize with the given values."""
        self.button = button

    def __str__(self) -> str:
        return f"{{self.__class__.__name__}}({{self.button.name}})"


class ReceivedRestart(Event):
    """Capture the event that we want to restart the game."""

    def __str__(self) -> str:
        return self.__class__.__name__
'''
    )

    write_or_raise_if_exists(
        module_dir / "common.py",
        '''\
"""Provide common functions and data structures used throughout the program."""

from typing import NoReturn


def assert_never(value: NoReturn) -> NoReturn:
    """
    Signal to mypy to perform an exhaustive matching.

    Please see the following page for more details:
    https://hakibenita.com/python-mypy-exhaustive-checking
    """
    assert False, f"Unhandled value: {value} ({type(value).__name__})"
'''
    )

    ci_dir = repo_root / "continuous_integration"
    ci_dir.mkdir(exist_ok=True)

    write_or_raise_if_exists(
        ci_dir / "precommit.py",
        f'''\
#!/usr/bin/env python3

"""Run pre-commit checks on the repository."""

import argparse
import enum
import os
import pathlib
import shlex
import subprocess
import sys
from typing import Optional, Mapping, Sequence


# pylint: disable=unnecessary-comprehension


class Step(enum.Enum):
    """Enumerate different pre-commit steps."""

    REFORMAT = "reformat"
    MYPY = "mypy"
    PYLINT = "pylint"
    TEST = "test"
    DOCTEST = "doctest"
    CHECK_INIT_AND_SETUP_COINCIDE = "check-init-and-setup-coincide"


def call_and_report(
    verb: str,
    cmd: Sequence[str],
    cwd: Optional[pathlib.Path] = None,
    env: Optional[Mapping[str, str]] = None,
) -> int:
    """
    Wrap a subprocess call with the reporting to STDERR if it failed.

    Return 1 if there is an error and 0 otherwise.
    """
    cmd_str = " ".join(shlex.quote(part) for part in cmd)

    if cwd is not None:
        print(f"Executing from {{cwd}}: {{cmd_str}}")
    else:
        print(f"Executing: {{cmd_str}}")

    exit_code = subprocess.call(cmd, cwd=str(cwd) if cwd is not None else None, env=env)

    if exit_code != 0:
        print(
            f"Failed to {{verb}} with exit code {{exit_code}}: {{cmd_str}}", file=sys.stderr
        )

    return exit_code


def main() -> int:
    """Execute entry_point routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--overwrite",
        help="Try to automatically fix the offending files (e.g., by re-formatting).",
        action="store_true",
    )
    parser.add_argument(
        "--select",
        help=(
            "If set, only the selected steps are executed. "
            "This is practical if some of the steps failed and you want to "
            "fix them in isolation. "
            "The steps are given as a space-separated list of: "
            + " ".join(value.value for value in Step)
        ),
        metavar="",
        nargs="+",
        choices=[value.value for value in Step],
    )
    parser.add_argument(
        "--skip",
        help=(
            "If set, skips the specified steps. "
            "This is practical if some of the steps passed and "
            "you want to fix the remainder in isolation. "
            "The steps are given as a space-separated list of: "
            + " ".join(value.value for value in Step)
        ),
        metavar="",
        nargs="+",
        choices=[value.value for value in Step],
    )

    args = parser.parse_args()

    overwrite = bool(args.overwrite)

    selects = (
        [Step(value) for value in args.select]
        if args.select is not None
        else [value for value in Step]
    )
    skips = [Step(value) for value in args.skip] if args.skip is not None else []

    repo_root = pathlib.Path(os.path.realpath(__file__)).parent.parent

    if Step.REFORMAT in selects and Step.REFORMAT not in skips:
        print("Re-formatting...")
        reformat_targets = [
            {repr(module_name)},
            "continuous_integration",
            "tests",
            "setup.py",
        ]

        if overwrite:
            exit_code = call_and_report(
                verb="black",
                cmd=["black"] + reformat_targets,
                cwd=repo_root,
            )
            if exit_code != 0:
                return 1
        else:
            exit_code = call_and_report(
                verb="check with black",
                cmd=["black", "--check"] + reformat_targets,
                cwd=repo_root,
            )
            if exit_code != 0:
                return 1
    else:
        print("Skipped re-formatting.")

    if Step.MYPY in selects and Step.MYPY not in skips:
        print("Mypy'ing...")
        mypy_targets = [
            {repr(module_name)},
            "tests",
            "continuous_integration",
        ]
        config_file = pathlib.Path("continuous_integration") / "mypy.ini"

        exit_code = call_and_report(
            verb="mypy",
            cmd=["mypy", "--strict", "--config-file", str(config_file)] + mypy_targets,
            cwd=repo_root,
        )
        if exit_code != 0:
            return 1
    else:
        print("Skipped mypy'ing.")

    if Step.PYLINT in selects and Step.PYLINT not in skips:
        print("Pylint'ing...")
        pylint_targets = [
            {repr(module_name)},
            "tests",
            "continuous_integration",
        ]
        rcfile = pathlib.Path("continuous_integration") / "pylint.rc"

        exit_code = call_and_report(
            verb="pylint",
            cmd=["pylint", f"--rcfile={{rcfile}}"] + pylint_targets,
            cwd=repo_root,
        )
        if exit_code != 0:
            return 1
    else:
        print("Skipped pylint'ing.")

    if Step.TEST in selects and Step.TEST not in skips:
        print("Testing...")
        env = os.environ.copy()
        env["ICONTRACT_SLOW"] = "true"

        exit_code = call_and_report(
            verb="execute unit tests",
            cmd=[
                "coverage",
                "run",
                "--source",
                {repr(module_name)},
                "-m",
                "unittest",
                "discover",
            ],
            cwd=repo_root,
            env=env,
        )
        if exit_code != 0:
            return 1

        _ = call_and_report(verb="report the coverage", cmd=["coverage", "report"])

        # NOTE (mristin, {today}):
        # Ignore a return code != 0 since coverage report returns 1 if there are no
        # tests.
    else:
        print("Skipped testing.")

    if Step.DOCTEST in selects and Step.DOCTEST not in skips:
        print("Doctest'ing...")

        doc_files = ["README.rst"]

        exit_code = call_and_report(
            verb="doctest",
            cmd=[sys.executable, "-m", "doctest"] + doc_files,
            cwd=repo_root,
        )
        if exit_code != 0:
            return 1

        for pth in (repo_root / {repr(module_name)}).glob("**/*.py"):
            if pth.name == "__main__.py":
                continue

            # NOTE (mristin, {today}):
            # The subprocess calls are expensive, call only if there is an actual
            # doctest
            text = pth.read_text(encoding="utf-8")
            if ">>>" in text:
                exit_code = call_and_report(
                    verb="doctest",
                    cmd=[sys.executable, "-m", "doctest", str(pth)],
                    cwd=repo_root,
                )
                if exit_code != 0:
                    return 1
    else:
        print("Skipped doctest'ing.")

    if (
        Step.CHECK_INIT_AND_SETUP_COINCIDE in selects
        and Step.CHECK_INIT_AND_SETUP_COINCIDE not in skips
    ):
        print("Checking that {module_name}/__init__.py and setup.py coincide...")
        exit_code = call_and_report(
            verb="check that {module_name}/__init__.py and setup.py coincide",
            cmd=[
                sys.executable,
                "continuous_integration/check_init_and_setup_coincide.py",
            ],
            cwd=repo_root,
        )
        if exit_code != 0:
            return 1
    else:
        print("Skipped checking that {module_name}/__init__.py and setup.py coincide.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
'''
    )

    write_or_raise_if_exists(
        ci_dir / "check_init_and_setup_coincide.py",
        f'''\
#!/usr/bin/env python3

"""Check that the distribution and {module_name}/__init__.py are in sync."""

import os
import pathlib
import subprocess
import sys
from typing import Optional, Dict

import {module_name}


def main() -> int:
    """Execute the main routine."""
    repo_root = pathlib.Path(os.path.realpath(__file__)).parent.parent

    setup_py_pth = repo_root / "setup.py"
    if not setup_py_pth.exists():
        raise RuntimeError(f"Could not find_our_type the setup.py: {{setup_py_pth}}")

    success = True

    ##
    # Check basic fields
    ##

    setup_py_map = dict()  # type: Dict[str, str]

    fields = ["version", "author", "license", "description"]
    for field in fields:
        out = subprocess.check_output(
            [sys.executable, str(repo_root / "setup.py"), f"--{{field}}"],
            encoding="utf-8",
        ).strip()

        setup_py_map[field] = out

    if setup_py_map["version"] != {module_name}.__version__:
        print(
            f"The version in the setup.py is {{setup_py_map['version']}}, "
            f"while the version in {module_name}/__init__.py is: "
            f"{{{module_name}.__version__}}",
            file=sys.stderr,
        )
        success = False

    if setup_py_map["author"] != {module_name}.__author__:
        print(
            f"The author in the setup.py is {{setup_py_map['author']}}, "
            f"while the author in {module_name}/__init__.py is: "
            f"{{{module_name}.__author__}}",
            file=sys.stderr,
        )
        success = False

    if setup_py_map["license"] != {module_name}.__license__:
        print(
            f"The license in the setup.py is {{setup_py_map['license']}}, "
            f"while the license in {module_name}/__init__.py is: "
            f"{{{module_name}.__license__}}",
            file=sys.stderr,
        )
        success = False

    if setup_py_map["description"] != {module_name}.__doc__:
        print(
            f"The description in the setup.py is {{setup_py_map['description']}}, "
            f"while the description in {module_name}/__init__.py is: "
            f"{{{module_name}.__doc__}}",
            file=sys.stderr,
        )
        success = False

    ##
    # Classifiers need special attention as there are multiple.
    ##

    # This is the map from the distribution to expected status in __init__.py.
    status_map = {{
        "Development Status :: 1 - Planning": "Planning",
        "Development Status :: 2 - Pre-Alpha": "Pre-Alpha",
        "Development Status :: 3 - Alpha": "Alpha",
        "Development Status :: 4 - Beta": "Beta",
        "Development Status :: 5 - Production/Stable": "Production/Stable",
        "Development Status :: 6 - Mature": "Mature",
        "Development Status :: 7 - Inactive": "Inactive",
    }}

    classifiers = (
        subprocess.check_output(
            [sys.executable, str(setup_py_pth), "--classifiers"], encoding="utf-8"
        )
        .strip()
        .splitlines()
    )

    status_classifier = None  # type: Optional[str]
    for classifier in classifiers:
        if classifier in status_map:
            status_classifier = classifier
            break

    if status_classifier is None:
        print(
            "Expected a status classifier in setup.py "
            "(e.g., 'Development Status :: 3 - Alpha'), but found none.",
            file=sys.stderr,
        )
        success = False
    else:
        expected_status_in_init = status_map[status_classifier]

        if expected_status_in_init != {module_name}.__status__:
            print(
                f"Expected status {{expected_status_in_init}} "
                f"according to setup.py in {module_name}/__init__.py, "
                f"but found: {{{module_name}.__status__}}"
            )
            success = False

    if not success:
        return -1

    return 0


if __name__ == "__main__":
    sys.exit(main())
'''
    )

    write_or_raise_if_exists(
        ci_dir / "mypy.ini",
        '''\
[mypy]

[mypy-pygame.freetype]
ignore_missing_imports = True
'''
    )

    write_or_raise_if_exists(
        ci_dir / "pylint.rc",
        '''\
[TYPECHECK]
ignored-modules = numpy
ignored-classes = numpy,PurePath

[FORMAT]
max-line-length=120

[MESSAGES CONTROL]
disable=too-few-public-methods,len-as-condition,duplicate-code,no-else-raise,no-else-return,too-many-locals,too-many-branches,too-many-nested-blocks,too-many-return-statements,unsubscriptable-object,not-an-iterable,broad-except,too-many-statements,protected-access,unnecessary-pass,too-many-statements,too-many-arguments,no-member,too-many-instance-attributes,too-many-lines,undefined-variable,unnecessary-lambda,assignment-from-none,useless-return,unused-argument,too-many-boolean-expressions,consider-using-f-string,use-dict-literal,invalid-name,no-else-continue,no-else-break,unneeded-not,too-many-public-methods,c-extension-no-member
'''
    )

    test_dir = repo_root / "tests"
    test_dir.mkdir(exist_ok=True)

    write_or_raise_if_exists(test_dir / "__init__.py", "")

    return 0


if __name__ == "__main__":
    sys.exit(main())
