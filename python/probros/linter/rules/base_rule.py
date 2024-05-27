import ast
from abc import ABC, abstractmethod

from diagnostic import Diagnostic


class BaseRule(ABC):
    """Abstract base class for defining linter rules.

    This class serves as a blueprint for creating specific rules that check for
    issues in the nodes. Each rule must override the `message` attribute and
    implement the `check` method.

    Attributes:
        message: A description of the rule, which may be used for diagnostic
            messages in case the rule is violated.
    """

    message: str

    @classmethod
    @abstractmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        """Check the given node for violations of a rule.

        This method must be implemented by subclasses to define the specific
        logic for checking the given node. If any message is used for any
        diagnostics or feedback, use the `message` attribute of the `cls`
        argument.

        Args:
            node: The AST node to check.

        Returns:
            A diagnostic instance if the node violates the rule, otherwise
            `None`.
        """
        raise NotImplementedError("Subclasses must implement this.")
