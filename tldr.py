import sys
import os
import re
from argparse import ArgumentParser
from pathlib import Path
from typing import List, Optional, Tuple
from termcolor import colored
from collections.abc import Iterable
from termcolor._types import Color, Highlight, Attribute
from typing import cast, Match

DEFAULT_COLORS = {
    "title1": "",
    "desc": "cyan blink",
    "title2": "underline",
    "code": "blue",
    "highlight": "yellow",
    "plain": "",
}

# See more details in the README:
# https://github.com/tldr-pages/tldr-python-client#colors
ACCEPTED_COLORS = ["blue", "green", "yellow", "cyan", "magenta", "white", "grey", "red"]

ACCEPTED_COLOR_BACKGROUNDS = [
    "on_blue",
    "on_cyan",
    "on_magenta",
    "on_white",
    "on_grey",
    "on_yellow",
    "on_red",
    "on_green",
]

ACCEPTED_COLOR_ATTRS = ["reverse", "blink", "dark", "concealed", "underline", "bold"]

SPACES = 4

CODE_SPLIT_REGEX = re.compile(r"(?P<code>~.+?~)")
CODE_REGEX = re.compile(r"(?:~)(?P<code>.+?)(?:~)")
HIGHLIGHT_SPLIT_REGEX = re.compile(r"(?P<highlight>=.+?=)")
HIGHLIGHT_REGEX = re.compile(r"(?:=)(?P<highlight>.+?)(?:=)")


def get_commands() -> List[str]:
    commands = ["hello"]
    return commands


def colors_of(
    key: str,
) -> Tuple[Optional[Color], Optional[Highlight], Optional[Iterable[Attribute]]]:
    values = DEFAULT_COLORS[key].strip().split()
    color = None
    on_color = None
    attrs = []
    for value in values:
        if value in ACCEPTED_COLORS:
            color = value
        elif value in ACCEPTED_COLOR_BACKGROUNDS:
            on_color = value
        elif value in ACCEPTED_COLOR_ATTRS:
            attrs.append(value)
    return (
        cast(Optional[Color], color),
        cast(Optional[Highlight], on_color),
        cast(Optional[Iterable[Attribute]], attrs),
    )


def color_code(text: Match) -> str:
    return colored(text.group("code"), *colors_of("code"))


def color_highlight(text: Match) -> str:
    # Use ANSI escapes to enable italics at the start and disable at the end
    # Also use the color yellow to differentiate from the default green
    return colored(text.group("highlight"), *colors_of("highlight"))


def handle_code(line: str) -> str:
    elements = []
    for item in CODE_SPLIT_REGEX.split(line):
        item, replaced = CODE_REGEX.subn(color_code, item)
        if not replaced:
            item = colored(item, *colors_of("plain"))
        elements.append(item)

    line = "".join(elements)
    return line


def handle_highlight(line: str) -> str:
    elements = []
    for item in HIGHLIGHT_SPLIT_REGEX.split(line):
        item, replaced = HIGHLIGHT_REGEX.subn(color_highlight, item)
        if not replaced:
            item = colored(item, *colors_of("plain"))
        elements.append(item)

    line = "".join(elements)
    return line


def output(page: List[bytes]) -> None:
    for line in page:
        line = line.rstrip().decode("utf-8")

        if line.startswith("* "):
            line = colored(line.replace("* ", "", 1), *colors_of("title1"))
            sys.stdout.buffer.write(line.encode("utf-8"))

        elif line.startswith("** "):
            line = colored(line.replace("** ", "", 1), *colors_of("title2"))
            sys.stdout.buffer.write(line.encode("utf-8"))

        elif line.startswith(": "):
            line = colored(line.replace(": ", "", 1), *colors_of("desc"))
            sys.stdout.buffer.write(line.encode("utf-8"))

        else:
            leading_spaces = len(line) - len(line.lstrip())
            line = line.lstrip()

            if line.startswith("- "):
                line = line.replace("- ", "◦ ", 1)

            if "~" in line:
                line = handle_code(line)

            if "=" in line:
                line = handle_highlight(line)

            line = " " * (SPACES + leading_spaces) + line
            sys.stdout.buffer.write(line.encode("utf-8"))
        print()
    print()


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="tldr",
        usage="tldr command [options]",
        description="Python command line client for tldr",
    )

    parser.add_argument(
        "command", type=str, nargs="*", help="command to lookup", metavar="command"
    )

    return parser


def main() -> None:
    parser = create_parser()

    options = parser.parse_args()

    if len(sys.argv) == 1:
        print(" | ".join(get_commands()))
    else:
        # render local org files
        file_name = "-".join(options.command)
        proj_path = os.path.abspath(os.path.dirname(__file__))
        file_path = Path(proj_path + "/pages/" + file_name + ".org")
        if file_path.exists():
            with file_path.open(encoding="utf-8") as open_file:
                output(open_file.read().encode("utf-8").splitlines())
        else:
            print("No such command")


def tldr() -> None:
    try:
        main()
    except KeyboardInterrupt:
        print("\nExited on keyboard interrupt.")


if __name__ == "__main__":
    tldr()
