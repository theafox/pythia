import ast

from diagnostic import Diagnostic

from .base import BaseRule
from .utils import Address, is_function_called


class RestrictSampleCallStructureRule(BaseRule):

    _NAME = "sample"

    message = f"Usage: `{_NAME}(<{Address.representation()}>, <distribution>)`"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        if not is_function_called(node, cls._NAME):
            return None
        match node:
            case ast.Call(
                args=[
                    address,
                    _,  # TODO: restrict distributions
                ],
                keywords=[],
            ) if Address.is_address(address):
                return None
            case _:
                return Diagnostic.from_node(node, message=cls.message)


class RestrictObserveCallStructureRule(BaseRule):

    _NAME = "observe"
    _SECOND_ARGUMENT = "address"
    _THIRD_ARGUMENT = "distribution"

    message = (
        f"Usage: `{_NAME}(<data>"
        f"[, [{_SECOND_ARGUMENT}=]<{Address.representation()}>"
        f"[, [{_THIRD_ARGUMENT}=]<distribution>]])`"
    )

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        if not is_function_called(node, cls._NAME):
            return None
        match node:
            # No address given.
            case ast.Call(
                args=[_],  # any expression as data
                keywords=([] | [ast.keyword(arg=cls._THIRD_ARGUMENT)]),
            ):
                return None
            # Address given.
            case (
                # One positional argument.
                ast.Call(
                    args=[_],  # any expression as data
                    keywords=(
                        [
                            ast.keyword(
                                arg=cls._SECOND_ARGUMENT,
                                value=address,
                            )
                        ]
                        | [
                            ast.keyword(
                                arg=cls._SECOND_ARGUMENT,
                                value=address,
                            ),
                            ast.keyword(arg=cls._THIRD_ARGUMENT),
                        ]
                        | [
                            ast.keyword(arg=cls._THIRD_ARGUMENT),
                            ast.keyword(
                                arg=cls._SECOND_ARGUMENT,
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
                        []  # the third remaining arguments is optional
                        | [ast.keyword(arg=cls._THIRD_ARGUMENT)]
                    ),
                )
                # Three positional arguments.
                | ast.Call(
                    args=[
                        _,  # any expression as data
                        address,
                        _,  # any of the distributions
                    ],
                    keywords=[],
                )
            ) if Address.is_address(address):
                return None
            case _:
                return Diagnostic.from_node(node, message=cls.message)
