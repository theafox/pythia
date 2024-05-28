import ast

from diagnostic import Diagnostic

from .base import BaseRule


class RestrictObserveCallRule(BaseRule):

    message = (
        "Observe usage: "
        "`observe(<data>, <str | IndexedAddress(...)>[, <distribution>])`"
    )

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        match node:
            case ast.Call(
                func=(ast.Name(id="observe") | ast.Attribute(attr="observe")),
                args=[
                    _,  # any expression as data
                    str()
                    | ast.Call(
                        func=(
                            ast.Name(id="IndexedAddress")
                            | ast.Attribute(attr="IndexedAddress")
                        )
                    ),
                    _,  # any of the distributions
                ],
            ):
                return None
            case ast.Call(
                func=(ast.Name(id="observe") | ast.Attribute(attr="observe"))
            ):
                return Diagnostic.from_node(node, message=cls.message)
            case _:
                return None
