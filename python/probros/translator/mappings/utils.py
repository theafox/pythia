import ast
from typing import Callable


def get_name(node: ast.expr, /, flat_name_only: bool = False) -> str:
    match node:
        case ast.Name(id=called) if flat_name_only:
            return called
        case (
            ast.Name(id=called)
            | ast.Attribute(attr=called)
        ) if not flat_name_only:
            return called
        case _:
            return str(node)


def is_function_called(
    node: ast.AST,
    name: str,
    /,
    has_args: Callable[[list[ast.expr]], bool] = lambda _: True,
    has_kwargs: Callable[[list[ast.keyword]], bool] = lambda _: True,
    is_flat_name: bool = False,
) -> bool:
    match node:
        case ast.Call(
            func=function,
            args=arguments,
            keywords=keyword_arguments,
        ) if (
            get_name(function) == name
            and has_args(arguments)
            and has_kwargs(keyword_arguments)
            and (
                not is_flat_name
                or (is_flat_name and isinstance(node.func, ast.Name))
            )
        ):
            return True
        case _:
            return False
