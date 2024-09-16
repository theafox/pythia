"""Utility functions, classes, etc. for defining rules.

The components of this file are written for and intended to be used for the
definition of rules.
"""

import ast
from typing import Callable, override


def is_function_called(
    node: ast.AST,
    name: str,
    has_args: Callable[[list[ast.expr]], bool] = lambda *args: True,
    has_kwargs: Callable[[list[ast.keyword]], bool] = lambda *args: True,
) -> bool:
    """Check if the given node is a function call with the given properties.

    This checks for both, direct function calls, i.e. `myname(...)`, and
    through attributes, i.e. `mypackage.myname(...)`.

    Args:
        node: The AST node to check.
        name: The name of the function to check for.
        has_args: A callable to check whether the arguments are valid.
        has_kwargs: A callable to check whether the keyword arguments are
            valid.

    Returns:
        bool: `True` if the node is a call to that specified function, `False`
        otherwise.
    """
    match node:
        case ast.Call(
            func=(ast.Name(id=called) | ast.Attribute(attr=called)),
            args=arguments,
            keywords=keyword_arguments,
        ) if (
            called == name
            and has_args(arguments)
            and has_kwargs(keyword_arguments)
        ):
            return True
        case _:
            return False


class classproperty(property):
    """A decorator to create class-level properties.

    This is a replacement for the (since python@3.13) deprecated decorator
    combination of `classmethod` and `property`.

    See:
        Inspired by Denis Ryzhkov at https://stackoverflow.com/a/13624858
    """

    @override
    def __get__(self, _, owner):
        """Retrieve the value of the class property.

        Args:
            instance: The called instance of the class. (ignored)
            owner: The class that owns the property.

        Returns:
            The result of calling the getter function with the class as its
            argument.
        """
        return self.fget(owner)


class Address:
    """A utility class for working with address-representations.

    This class is designed to be static encapsulation of address-related
    features and should not be instantiated.
    """

    _ADDRESS_CALL = "IndexedAddress"

    @override
    def __new__(cls):
        """Prevent instantiation of this class.

        Raises:
            RuntimeError: Always raised to prevent instantiation.
        """
        raise RuntimeError(f"{cls} is a static class.")

    @classmethod
    def is_address(cls, node: ast.AST) -> bool:
        """Check whether a given node is an address.

        Args:
            node: The AST node check

        Returns:
            `True` if the node represents an address, `False` otherwise.
        """
        match node:
            case ast.Constant(value=str()):
                return True
            case ast.Call(
                func=(ast.Name(id=called) | ast.Attribute(attr=called))
            ) if called == cls._ADDRESS_CALL:
                return True
            case _:
                return False

    @classmethod
    def representation(cls) -> str:
        """Get the string representation of the address type.

        Returns:
            The string representation of the address type.
        """
        return f"str | {cls._ADDRESS_CALL}(...)"


class Distribution:
    """A utility class for working with distribution-representations.

    This class is designed to be static encapsulation of address-related
    features and should not be instantiated.
    """

    _DISTRIBUTIONS = [
        "Dirac",
        "Beta",
        "Cauchy",
        "Exponential",
        "Gamma",
        "HalfCauchy",
        "HalfNormal",
        "InverseGamma",
        "Normal",
        "StudentT",
        "Uniform",
        "Bernoulli",
        "Binomial",
        "DiscreteUniform",
        "Geometric",
        "HyperGeometric",
        "Poisson",
        "Dirichlet",
        "MultivariateNormal",
    ]

    @classproperty
    def _WRAPPING_DISTRIBUTIONS(
        cls,
    ) -> list[
        tuple[
            str,
            Callable[[list[ast.expr]], bool],
            Callable[[list[ast.keyword]], bool],
        ],
    ]:
        """Define how "wrapping" distributions are specified.

        This provides a list of tuples, where each tuple represents some
        wrapping distribution. Each tuple contains the following information
        (in that order):

        - The name of the wrapping distribution function.
        - A function to check whether the passed arguments are valid.
        - A function to check whether the passed keyword arguments are valid.

        Returns:
            A list of tuples describing the wrapping distributions.
        """
        return [
            (
                "IID",
                lambda args: len(args) == 2
                and cls._is_base_distribution(args[0]),
                lambda kwargs: not kwargs,
            ),
        ]

    @override
    def __new__(cls):
        """Prevent instantiation of this class.

        Raises:
            RuntimeError: Always raised to prevent instantiation.
        """
        raise RuntimeError(f"{cls} is a static class.")

    @classmethod
    def is_distribution(cls, node: ast.AST) -> bool:
        """Check whether a given node is an distribution.

        Args:
            node: The AST node check

        Returns:
            `True` if the node represents a distribution, `False` otherwise.
        """
        return cls._is_base_distribution(node) or any(
            is_function_called(
                node,
                wrapping[0],
                has_args=wrapping[1],
                has_kwargs=wrapping[2],
            )
            for wrapping in cls._WRAPPING_DISTRIBUTIONS
        )

    @classmethod
    def _is_base_distribution(cls, node: ast.AST) -> bool:
        """Check whether a given node is a simple/base distribution.

        Where "simple"/"base" distribution shall mean, no broadcasted or
        otherwise "extended" distribution form.

        Args:
            node: The AST node check

        Returns:
            `True` if the node represents a distribution, `False` otherwise.
        """
        return any(
            is_function_called(node, distribution)
            for distribution in cls._DISTRIBUTIONS
        )

    @classmethod
    def representation(cls) -> str:
        """Get the string representation of the distribution type.

        Returns:
            The string representation of the distribution type.
        """
        return "distribution"
