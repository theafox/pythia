import ast
import logging as log
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Self


class Severity(Enum):
    """This represents the severity of diagnostics.

    Attributes:
        WARNING: Indicates a warning-level severity.
        ERROR: Indicates a warning-level severity.
    """

    WARNING = 10
    ERROR = 20

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
        return (
            f"{self.line:4d}:{self.column}:\t{self.severity}: {self.message}"
        )

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


class BaseLinter(ABC, ast.NodeVisitor):
    """A base class for linters to validate some code.

    Attributes:
        diagnostics: A list to store diagnostics.
    """

    @abstractmethod
    def __init__(self, **kwargs) -> None:
        """Abstract initialization method.

        Args:
            **kwargs: Any further arguments, those will be handed to the
                initialization method of any super classes.
        """

        self.diagnostics: list[Diagnostic] = []
        super().__init__(**kwargs)

    def run(self, target: ast.AST | str) -> list[Diagnostic]:
        """Run the linter and receive any diagnostics.

        In case `node` is given as a string, (i) attempt to interpret it as a
        file-path to read and lint the file, if this fails, (ii) try to lint
        the string itself.

        Args:
            target: The file or code on which to run the linter on.

        Returns:
            A list of any diagnostics found.
        """

        if isinstance(target, str):
            # (i) attempt to interpret `target` as a file-path…
            log.debug(
                f"Received {target[:25]!a}… as a string,"
                " try interpreting it as a file-path."
            )
            if os.path.isfile(target):
                log.debug(
                    f"Identified {target[:25]!a}… as a file,"
                    " reading the contents."
                )
                try:
                    with open(target, "r") as file:
                        target = file.read()
                except IOError as error:
                    log.debug(
                        f"Failed to read {target[:25]!a}… as a file: {error}"
                    )

            # (ii) attempt to parse `target` as code…
            log.debug(f"Parsing {target[:25]!a}… as code.")
            try:
                target = ast.parse(target)
            except ValueError as error:
                log.fatal(
                    f"Failed to parse {str(target)[:25]!a}… as code,"
                    f" aborting {self.__class__.__name__}: {error}"
                )
                return []

        log.debug(
            f"Running {self.__class__.__name__} on"
            f" node {ast.dump(target)[:25]}…."
        )

        self.diagnostics = []
        self.visit(target)

        log.debug(
            f"{self.__class__.__name__} finished,"
            f" got {len(self.diagnostics)} diagnostics."
        )

        diagnostics = self.diagnostics
        self.diagnostics = []
        return diagnostics
