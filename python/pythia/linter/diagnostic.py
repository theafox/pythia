"""`Diagnostic` class and any of its dependencies.

The `Diagnostic` class is intended to store all the necessary information of an
error, warning, etc. See their respective documentation for further details.
"""

import ast
from dataclasses import dataclass
from enum import IntEnum
from typing import Self, override


class Severity(IntEnum):
    """This represents the severity of diagnostics.

    Attributes:
        ERROR: Indicates a warning-level severity.
        WARNING: Indicates a warning-level severity.
        INFORMATION: Indicates an information-level severity.
        HINT: Indicates a hint-level severity.
    """

    ERROR = 40
    WARNING = 30
    INFORMATION = 20
    HINT = 10

    @override
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

    @override
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
        node: ast.stmt
        | ast.expr
        | ast.excepthandler
        | ast.arg
        | ast.keyword
        | ast.alias
        | ast.pattern
        | ast.type_param,
        message: str,
        severity: Severity = Severity.ERROR,
    ) -> Self:
        """Create a diagnostic from an AST node.

        The line, column, line end, and column end are extracted from the node.
        In case the line/column end is not given, they are set to equal the
        start line/column.

        Args:
            node: The node from which to extract the positional information.
            message: The message for this diagnostic instance.
            severity: The severity level for this diagnostic instance.
                (defaults to `Severity.ERROR`)

        Returns:
            A diagnostic instance with the positional information from the node
            and the provided message as the message.
        """
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
