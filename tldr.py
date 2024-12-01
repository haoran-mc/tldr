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

LEADING_SPACES_NUM = 2

EXAMPLE_SPLIT_REGEX = re.compile(r"(?P<list>`.+?`)")
EXAMPLE_REGEX = re.compile(r"(?:`)(?P<list>.+?)(?:`)")
COMMAND_SPLIT_REGEX = re.compile(r"(?P<param>{{.+?}*}})")
PARAM_REGEX = re.compile(r"(?:{{)(?P<param>.+?)(?:}})")


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


def output(page: List[bytes]) -> None:
    def emphasise_example(x: Match) -> str:
        # Use ANSI escapes to enable italics at the start and disable at the end
        # Also use the color yellow to differentiate from the default green
        return "\x1b[3m" + colored(x.group("list"), "yellow") + "\x1b[23m"

    for line in page:
        line = line.rstrip().decode("utf-8")

        if len(line) == 0:
            continue

        # Handle the command title
        elif line[0] == "#":
            line = (
                "\n"
                + " " * LEADING_SPACES_NUM
                + colored(line.replace("# ", ""), *colors_of("title"))
                + "\n"
            )
            sys.stdout.buffer.write(line.encode("utf-8"))

        # Handle the command description
        elif line[0] == ">":
            line = " " * (LEADING_SPACES_NUM - 1) + colored(
                line.replace(">", "").replace("<", ""), *colors_of("desc")
            )
            sys.stdout.buffer.write(line.encode("utf-8"))

        # Handle an example description
        elif line[0] == "-":
            # Stylize text within backticks using yellow italics
            if "`" in line:
                elements = ["\n", " " * LEADING_SPACES_NUM]

                for item in EXAMPLE_SPLIT_REGEX.split(line):
                    item, replaced = EXAMPLE_REGEX.subn(emphasise_example, item)
                    if not replaced:
                        item = colored(item, *colors_of("list"))
                    elements.append(item)

                line = "".join(elements)

            # Otherwise, use the same colour for the whole line
            else:
                line = (
                    "\n"
                    + " " * LEADING_SPACES_NUM
                    + colored(line, *colors_of("list"))
                )

            sys.stdout.buffer.write(line.encode("utf-8"))

        # Handle an example command
        elif line[0] == "`":
            line = line[1:-1]  # Remove backticks for parsing

            # Handle escaped placeholders first
            line = line.replace(r"\{\{", "__ESCAPED_OPEN__")
            line = line.replace(r"\}\}", "__ESCAPED_CLOSE__")

            elements = [" " * 2 * LEADING_SPACES_NUM]
            for item in COMMAND_SPLIT_REGEX.split(line):
                item, replaced = PARAM_REGEX.subn(
                    lambda x: colored(x.group("param"), *colors_of("param")), item
                )
                if not replaced:
                    item = colored(item, *colors_of("code"))
                elements.append(item)

            line = "".join(elements)

            # Restore escaped placeholders
            line = line.replace("__ESCAPED_OPEN__", "{{")
            line = line.replace("__ESCAPED_CLOSE__", "}}")

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
