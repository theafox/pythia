"""A simple demonstration of the translator.

This showcases the translator using the examples of the thesis defining
_PyThia_.

Usage: This should be executed as a module, i.e.
    `python -m translator_demonstration [OPTIONS]`. In case any command-line
    arguments are provided, they are interpreted as the selection of target
    languages/frameworks to translate.

Author: T. Kaufmann <e12002221@student.tuwien.ac.at>
"""

from pathlib import Path

from translator import (
    Translator,
    default_gen_translator,
    default_pyro_translator,
    default_turing_translator,
)


def _get_available_translators() -> list[tuple[str, Translator]]:
    return [
        ("gen", default_gen_translator()),
        ("pyro", default_pyro_translator()),
        ("turing", default_turing_translator()),
    ]


def _get_code_pieces() -> list[str]:
    directory = Path(__file__).parent
    files = [
        file
        for file in directory.glob("*.py")
        if not file.name.startswith("_")
    ]
    files.sort()
    code_pieces: list[str] = []
    for file in files:
        with file.open() as stream:
            code_pieces.append(stream.read())
    return code_pieces


def _display_translation(
    code: str,
    *translators: tuple[str, Translator],
    width: int = 60,
    header_character: str = "=",
    subheader_character: str = "-",
) -> None:
    print(f"\n{" Original Code ":{header_character}^{width}}")
    print(code, end="")
    for name, translator in translators:
        print(f"\n{f" Translated: {name} ":{subheader_character}^{width}}")
        if translation := translator.translate_code(code):
            print(translation, end="")
    print("\n" + header_character * width)


if __name__ == "__main__":
    import sys

    from translator.__main__ import Verbosity, configure_logger

    configure_logger(Verbosity.NORMAL)
    translators = [
        (name, translator)
        for name, translator in _get_available_translators()
        if not (arguments := sys.argv[1:]) or name in arguments
    ]
    code_pieces = _get_code_pieces()
    for code in code_pieces:
        _display_translation(code, *translators)
