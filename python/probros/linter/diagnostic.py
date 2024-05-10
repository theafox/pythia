import ast
from dataclasses import dataclass
from enum import Enum
from typing import Self


class Severity(Enum):
    """This represents the severity of diagnostics.

    Attributes:
        WARNING: Indicates a warning-level severity.
        ERROR: Indicates a warning-level severity.
    """

    ERROR = 40
    WARNING = 30
    INFORMATION = 20
    HINT = 10

    def __str__(self) -> str:
        """Get the string representation of the severity.

        Returns:
            The string representation of the severity.
        """

        return str(self.name)


@dataclass(frozen=True, kw_only=True)
class Diagnostic:
    """A representation of diagnostics.

    Attributes:
        line: The line number of the diagnostic.
        end_line: The ending line number of the diagnostic.
        column: The column number of the diagnostic.
        end_column: The ending column number of the diagnostic.
        message: The message of the diagnostic.
        severity: The severity of the diagnostic.
    """

    line: int
    end_line: int
    column: int
    end_column: int
    message: str
    severity: Severity = Severity.ERROR

    def __str__(self) -> str:
        """Get a presentable representation of this diangostic.

        Returns:
            A one-line message including the line number, column number,
            severity, and message.
        """
        return f"{self.line:4d}:{self.column}: {self.severity}: {self.message}"

    @classmethod
    def from_node(
        cls,
        node: ast.AST,
        message: str,
        severity: Severity = Severity.ERROR,
    ) -> Self:
        return cls(
            line=node.lineno,
            end_line=(
                node.end_lineno
                if node.end_lineno and node.end_lineno >= node.lineno
                else node.lineno
            ),
            column=node.col_offset,
            end_column=(
                node.end_col_offset
                if node.end_col_offset
                and node.end_col_offset >= node.col_offset
                else node.col_offset
            ),
            message=message,
            severity=severity,
        )
