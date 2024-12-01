#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

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
    "title": "bold",
    "desc": "",
    "list": "green",
    "code": "red",
    "param": "",
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

SPACES = 2

EXAMPLE_SPLIT_REGEX = re.compile(r"(?P<list>`.+?`)")
EXAMPLE_REGEX = re.compile(r"(?:`)(?P<list>.+?)(?:`)")


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


def color_title(text: str) -> str:
    text = colored(text.replace("# ", ""), *colors_of("title")) + "\n"
    return text


def color_desc(text: str) -> str:
    text = colored(text.replace("> ", ""), *colors_of("desc")) + "\n"
    return text


def color_list(text: str) -> str:
    return text


def color_code(text: Match) -> str:
    return colored(text.group(), *colors_of("code"))


def color_highlight(text: Match) -> str:
    # Use ANSI escapes to enable italics at the start and disable at the end
    # Also use the color yellow to differentiate from the default green
    return "\x1b[3m" + colored(text.group(), "yellow") + "\x1b[23m"


def output(page: List[bytes]) -> None:
    for line in page:
        line = line.rstrip().decode("utf-8")

        if len(line) == 0:
            continue

        elif line[0] == "#":
            line = color_title(line)
            sys.stdout.buffer.write(line.encode("utf-8"))

        elif line[0] == ">":
            line = color_desc(line)
            sys.stdout.buffer.write(line.encode("utf-8"))

        elif line[0] == "-":
            # Stylize text within backticks using yellow italics
            if "`" in line:
                elements = ["\n", " " * SPACES]

                for item in EXAMPLE_SPLIT_REGEX.split(line):
                    item, replaced = EXAMPLE_REGEX.subn(color_highlight, item)
                    if not replaced:
                        item = colored(item, *colors_of("list"))
                    elements.append(item)

                line = "".join(elements)

            # Otherwise, use the same colour for the whole line
            else:
                line = "\n" + " " * SPACES + colored(line, *colors_of("list"))
            sys.stdout.buffer.write(line.encode("utf-8"))

        else:
            # has code
            if "`" in line:
                texts = []
                for item in EXAMPLE_SPLIT_REGEX.split(line):
                    item, replaced = EXAMPLE_REGEX.subn(color_code, item)
                    texts.append(item)
                line = "".join(texts)
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
        print("\n".join(get_commands()))
    else:
        # render local markdown files
        file_name = "-".join(options.command)
        proj_path = os.path.abspath(os.path.dirname(__file__))
        file_path = Path(proj_path + "/pages/" + file_name + ".md")
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
