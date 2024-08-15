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
    indentation: int
    contents: str

    _shiftwidth: str = field(default="    ", init=False)

    @override
    def __str__(self) -> str:
        return self._shiftwidth * self.indentation + self.contents


@dataclass
class Context:
    translator: "Translator"

    _indentation: int = field(default=0, init=False)
    _lines: list[Line] = field(default_factory=list, init=False)

    _unique_address_counter: ClassVar[int] = 0

    @staticmethod
    def unique_address() -> str:
        Context._unique_address_counter += 1
        return f"__context__unique_address_{Context._unique_address_counter}"

    def consolidated(self) -> str:
        return "\n".join(str(line) for line in self._lines)

    def line(self, line: str) -> None:
        self._lines.append(Line(self._indentation, line))

    @contextmanager
    def indented(self):
        try:
            self._indentation += 1
            yield
        finally:
            self._indentation -= 1
