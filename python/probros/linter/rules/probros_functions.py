import ast

from diagnostic import Diagnostic

from .base import BaseRule


class RestrictObserveCallStructureRule(BaseRule):

    _NAME = "observe"
    _SECOND_ARGUMENT = "address"
    _THIRD_ARGUMENT = "distribution"
    _ADDRESS_CALL = "IndexedAddress"

    message = (
        f"Usage: `{_NAME}(<data>"
        f"[, [{_SECOND_ARGUMENT}=]<str | {_ADDRESS_CALL}(...)>"
        f"[, [{_THIRD_ARGUMENT}=]<distribution>]])`"
    )

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        match node:
            case (
                # One positional argument.
                ast.Call(
                    func=(
                        ast.Name(id=cls._NAME) | ast.Attribute(attr=cls._NAME)
                    ),
                    args=[_],  # any expression as data
                    keywords=(
                        []  # both remaining arguments are optional
                        | [
                            ast.keyword(
                                arg=cls._SECOND_ARGUMENT,
                                value=(
                                    ast.Constant(value=str())
                                    | ast.Call(
                                        func=(
                                            ast.Name(id=cls._ADDRESS_CALL)
                                            | ast.Attribute(
                                                attr=cls._ADDRESS_CALL
                                            )
                                        )
                                    )
                                ),
                            )
                        ]
                        | [ast.keyword(arg=cls._THIRD_ARGUMENT)]
                        | [
                            ast.keyword(
                                arg=cls._SECOND_ARGUMENT,
                                value=(
                                    ast.Constant(value=str())
                                    | ast.Call(
                                        func=(
                                            ast.Name(id=cls._ADDRESS_CALL)
                                            | ast.Attribute(
                                                attr=cls._ADDRESS_CALL
                                            )
                                        )
                                    )
                                ),
                            ),
                            ast.keyword(arg=cls._THIRD_ARGUMENT),
                        ]
                        | [
                            ast.keyword(arg=cls._THIRD_ARGUMENT),
                            ast.keyword(
                                arg=cls._SECOND_ARGUMENT,
                                value=(
                                    ast.Constant(value=str())
                                    | ast.Call(
                                        func=(
                                            ast.Name(id=cls._ADDRESS_CALL)
                                            | ast.Attribute(
                                                attr=cls._ADDRESS_CALL
                                            )
                                        )
                                    )
                                ),
                            ),
                        ]
                    ),
                )
                # Two positional arguments.
                | ast.Call(
                    func=(
                        ast.Name(id=cls._NAME) | ast.Attribute(attr=cls._NAME)
                    ),
                    args=[
                        _,  # any expression as data
                        ast.Constant(value=str())
                        | ast.Call(
                            func=(
                                ast.Name(id=cls._ADDRESS_CALL)
                                | ast.Attribute(attr=cls._ADDRESS_CALL)
                            )
                        ),
                    ],
                    keywords=(
                        []  # the third remaining arguments is optional
                        | [ast.keyword(arg=cls._THIRD_ARGUMENT)]
                    ),
                )
                # Three positional arguments.
                | ast.Call(
                    func=(
                        ast.Name(id=cls._NAME) | ast.Attribute(attr=cls._NAME)
                    ),
                    args=[
                        _,  # any expression as data
                        ast.Constant(value=str())
                        | ast.Call(
                            func=(
                                ast.Name(id=cls._ADDRESS_CALL)
                                | ast.Attribute(attr=cls._ADDRESS_CALL)
                            )
                        ),
                        _,  # any of the distributions
                    ],
                    keywords=[],
                )
            ):
                return None
            case ast.Call(
                func=(ast.Name(id=cls._NAME) | ast.Attribute(attr=cls._NAME))
            ):
                return Diagnostic.from_node(node, message=cls.message)
            case _:
                return None
