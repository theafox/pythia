from contextlib import contextmanager
from dataclasses import dataclass, field
from itertools import chain
from typing import TYPE_CHECKING, ClassVar, override

# Import `Translator` only for the language-server and any linters since
# circular imports would become a problem otherwise. For this reason, use
# quotations around `Translator` when using it as an annotation.
if TYPE_CHECKING:
    from translator import Translator


@dataclass
class Line:
    """This represents a line of code.

    Attributes:
        indentation: The level of indentation.
        contents: The contents of this line.
    """

    indentation: int
    contents: str

    _shiftwidth: str = field(default="    ", init=False)

    @override
    def __str__(self) -> str:
        """Get the string representation of this line.

        Returns:
            The string representation of this line.
        """
        return self._shiftwidth * self.indentation + self.contents


@dataclass
class Context:
    """This represents the context during the translation process.

    This aggregates the lines which have been translated and stores any context
    relevant information and variables, such as a reference to the translator
    in use. This allows mappings which are passed a `Context` instance to use
    those context relevant variables like the translator for translation of
    sub-nodes.

    Further functionality of this class includes the addition of lines or
    multiple to a _preamble_ and _postamble_. Which will be added before and
    after the body of the translation respectively.

    Attributes:
        translator: The translator used in the translation process.
    """

    translator: "Translator._TranslatingTraverser"  # type: ignore

    _indentation: int = field(default=0, init=False)
    _lines: list[Line] = field(default_factory=list, init=False)
    _preamble: list[str] = field(default_factory=list, init=False)
    _postamble: list[str] = field(default_factory=list, init=False)

    _unique_address_counter: ClassVar[int] = 0

    @staticmethod
    def unique_address() -> str:
        """Get a unique address.

        Returns:
            A unique address compared to previous calls.
        """

        Context._unique_address_counter += 1
        return f"__context__unique_address_{Context._unique_address_counter}"

    def consolidated(self) -> str:
        """Get the consolidated resulting code.

        This includes the body and the pre- and postamble.

        Returns:
            Consolidated code of this `Context` instance.
        """

        return "\n".join(
            chain(
                self._preamble,
                map(str, self._lines),
                self._postamble,
            )
        )

    def line(self, line: str) -> None:
        """Append a line of code to the body.

        Args:
            line: The line of code to append to the body.
        """

        self._lines.append(Line(self._indentation, line))

    @contextmanager
    def indented(self):
        """A context manager to create an indented context."""
        try:
            self._indentation += 1
            yield
        finally:
            self._indentation -= 1

    @contextmanager
    def in_preamble(self, /, discard_if_present: bool = False):
        """Add code to the preamble.

        Args:
            discard_if_present: In case the provided code is already present,
                do not add it again. (Order and indentation of lines matters.)

        Yields:
            A `Context` variable which represents the preamble.
        """

        context = Context(self.translator)
        try:
            yield context
        finally:
            lines = context.consolidated()
            if lines and (
                not discard_if_present or lines not in self._preamble
            ):
                self._preamble.append(lines)

    @contextmanager
    def in_postamble(self, /, discard_if_present: bool = False):
        """Add code to the postamble.

        Args:
            discard_if_present: In case the provided code is already present,
                do not add it again. (Order and indentation of lines matters.)

        Yields:
            A `Context` variable which represents the postamble.
        """

        context = Context(self.translator)
        try:
            yield context
        finally:
            lines = context.consolidated()
            if lines and (
                not discard_if_present or lines not in self._postamble
            ):
                self._postamble.append(lines)
