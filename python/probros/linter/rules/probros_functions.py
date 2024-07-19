"""This module contains rules for validating probros-specific nodes.

Each rule is implemented as a class inheriting from `BaseRule`. Therefore, view
the documentation of that class in case of changes or additions.
"""

import ast
from typing import override

from diagnostic import Diagnostic

from .base import BaseRule
from .utils import Address, Distribution, is_function_called


class RestrictSampleCallStructureRule(BaseRule):
    _NAME = "sample"

    message = (
        f"Usage: `{_NAME}("
        f"<{Address.representation()}>"
        f", <{Distribution.representation()}>)`"
    )

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        if not is_function_called(node, cls._NAME):
            return None
        assert isinstance(node, ast.Call)  # `is_function_called` ensures this
        match node:
            case ast.Call(
                args=[
                    address,
                    distribution,
                ],
                keywords=[],
            ) if Address.is_address(address) and Distribution.is_distribution(
                distribution
            ):
                return None
            case _:
                return Diagnostic.from_node(node, message=cls.message)


class RestrictObserveCallStructureRule(BaseRule):
    _NAME = "observe"
    _ADDRESS = "address"
    _DISTRIBUTION = "distribution"

    message = (
        f"Usage: `{_NAME}(<data>"
        f"[, [{_ADDRESS}=]<{Address.representation()}>"
        f"[, [{_DISTRIBUTION}=]<{Distribution.representation()}>]])`"
    )

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        if not is_function_called(node, cls._NAME):
            return None
        assert isinstance(node, ast.Call)  # `is_function_called` ensures this
        match node:
            # Only `data`.
            case ast.Call(args=[_], keywords=[]):  # any expression as data
                return None
            # Only `address`.
            case ast.Call(
                args=[_],  # any expression as data
                keywords=[ast.keyword(arg=cls._ADDRESS, value=address)],
            ) if Address.is_address(address):
                return None
            # Only `distribution`.
            case ast.Call(
                args=[_],  # any expression as data
                keywords=[
                    ast.keyword(arg=cls._DISTRIBUTION, value=distribution)
                ],
            ) if Distribution.is_distribution(distribution):
                return None
            # All is given.
            case (
                # One positional argument.
                ast.Call(
                    args=[_],  # any expression as data
                    keywords=(
                        [
                            ast.keyword(
                                arg=cls._ADDRESS,
                                value=address,
                            ),
                            ast.keyword(
                                arg=cls._DISTRIBUTION,
                                value=distribution,
                            ),
                        ]
                        | [
                            ast.keyword(
                                arg=cls._DISTRIBUTION,
                                value=distribution,
                            ),
                            ast.keyword(
                                arg=cls._ADDRESS,
                                value=address,
                            ),
                        ]
                    ),
                )
                # Two positional arguments.
                | ast.Call(
                    args=[
                        _,  # any expression as data
                        address,
                    ],
                    keywords=(
                        ast.keyword(
                            arg=cls._DISTRIBUTION,
                            value=distribution,
                        ),
                    ),
                )
                # Three positional arguments.
                | ast.Call(
                    args=[
                        _,  # any expression as data
                        address,
                        distribution,
                    ],
                    keywords=[],
                )
            ) if Address.is_address(address) and Distribution.is_distribution(
                distribution
            ):
                return None
            case _:
                return Diagnostic.from_node(node, message=cls.message)


class RestrictFactorCallStructureRule(BaseRule):
    _NAME = "factor"
    _ADDRESS = "address"

    message = (
        f"Usage: `{_NAME}(<data>"
        f"[, [{_ADDRESS}=]<{Address.representation()}>])"
    )

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        if not is_function_called(node, cls._NAME):
            return None
        assert isinstance(node, ast.Call)  # `is_function_called` ensures this
        match node:
            # No address given.
            case ast.Call(args=[_], keywords=[]):
                return None
            # Address given.
            case (
                ast.Call(
                    args=[_, address],
                    keywords=[],
                )
                | ast.Call(
                    args=[_],
                    keywords=[ast.keyword(arg=cls._ADDRESS, value=address)],
                )
            ) if Address.is_address(address):
                return None
            case _:
                return Diagnostic.from_node(node, message=cls.message)


class RestrictIndexedAddressCallStructureRule(BaseRule):
    _NAME = "IndexedAddress"

    message = f"Usage: `{_NAME}(<address>, <index>, …)`"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        if not is_function_called(node, cls._NAME):
            return None
        assert isinstance(node, ast.Call)  # `is_function_called` ensures this
        match node:
            case ast.Call(
                args=[address, *indices],
                keywords=[],
            ) if Address.is_address(address) and indices:
                return None
            case _:
                return Diagnostic.from_node(node, message=cls.message)


class RestrictVectorConstructorCallStructureRule(BaseRule):
    _NAME = "Vector"
    _FILL = "fill"
    _TYPE = "t"

    # TODO: restrict further
    message = (
        f"Usage: `{_NAME}(<data>"
        f"[, [{_FILL}=]<data>"
        f"[, [{_TYPE}=]<data>]])`"
    )

    # TODO: restrict further
    # NOTE: also check whether `type` is allowed without `fill`
    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        if not is_function_called(node, cls._NAME):
            return None
        assert isinstance(node, ast.Call)  # `is_function_called` ensures this
        match node:
            case (
                ast.Call(
                    args=[_],
                    keywords=[],
                )
                | ast.Call(
                    args=[_],
                    keywords=[ast.keyword(arg=cls._FILL)],
                )
                | ast.Call(
                    args=[_],
                    keywords=[ast.keyword(arg=cls._TYPE)],
                )
                | ast.Call(
                    args=[_],
                    keywords=[
                        ast.keyword(arg=cls._FILL),
                        ast.keyword(arg=cls._TYPE),
                    ],
                )
                | ast.Call(
                    args=[_],
                    keywords=[
                        ast.keyword(arg=cls._TYPE),
                        ast.keyword(arg=cls._FILL),
                    ],
                )
                | ast.Call(
                    args=[_, _],
                    keywords=[ast.keyword(arg=cls._FILL)],
                )
                | ast.Call(
                    args=[_, _, _],
                    keywords=[],
                )
            ):
                return None
            case _:
                return Diagnostic.from_node(node, message=cls.message)


class RestrictArrayConstructorCallStructureRule(BaseRule):
    _NAME = "Array"
    _FILL = "fill"
    _TYPE = "t"

    # TODO: restrict further
    message = (
        f"Usage: `{_NAME}(<data>"
        f"[, [{_FILL}=]<data>"
        f"[, [{_TYPE}=]<data>]])`"
    )

    # TODO: restrict further
    # NOTE: also check whether `type` is allowed without `fill`
    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        if not is_function_called(node, cls._NAME):
            return None
        assert isinstance(node, ast.Call)  # `is_function_called` ensures this
        match node:
            case (
                ast.Call(
                    args=[_],
                    keywords=[],
                )
                | ast.Call(
                    args=[_],
                    keywords=[ast.keyword(arg=cls._FILL)],
                )
                | ast.Call(
                    args=[_],
                    keywords=[ast.keyword(arg=cls._TYPE)],
                )
                | ast.Call(
                    args=[_],
                    keywords=[
                        ast.keyword(arg=cls._FILL),
                        ast.keyword(arg=cls._TYPE),
                    ],
                )
                | ast.Call(
                    args=[_],
                    keywords=[
                        ast.keyword(arg=cls._TYPE),
                        ast.keyword(arg=cls._FILL),
                    ],
                )
                | ast.Call(
                    args=[_, _],
                    keywords=[ast.keyword(arg=cls._FILL)],
                )
                | ast.Call(
                    args=[_, _, _],
                    keywords=[],
                )
            ):
                return None
            case _:
                return Diagnostic.from_node(node, message=cls.message)
