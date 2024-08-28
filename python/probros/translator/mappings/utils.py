import ast
import inspect
from typing import Callable, Iterable

from context import Context


def get_name(node: ast.expr) -> str:
    match node:
        case ast.Name(id=called) | ast.Attribute(attr=called):
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


def organize_arguments(
    arguments: Iterable[ast.expr],
    keyword_arguments: Iterable[ast.keyword],
    /,
    argument_defaults: Iterable[ast.expr | Callable[[], ast.expr]] = [],
    keyword_argument_defaults: Iterable[
        str
        | tuple[int, str, ast.expr]
        | tuple[int, str, Callable[[], ast.expr]]
    ] = [],
) -> Iterable[ast.expr]:
    # Positional arguments.
    arguments = list(arguments)
    argument_defaults = list(argument_defaults)
    for default in argument_defaults[len(arguments) :]:
        arguments.append(default if not callable(default) else default())
    # Keyword arguments.
    keyword_dictionary = {
        keyword.arg: keyword.value for keyword in keyword_arguments
    }
    positional_defaults = sorted(
        [
            default
            for default in keyword_argument_defaults
            if isinstance(default, tuple)
        ],
        key=lambda default: default[0],
    )  # sort according to each given position.
    nonpositional_defaults = [
        default
        for default in keyword_argument_defaults
        if isinstance(default, str)
    ]
    for default in positional_defaults:
        position, name, default = default
        if len(arguments) == position - 1:
            arguments.append(
                keyword_dictionary.pop(name, default)
                if not callable(default)
                else keyword_dictionary.pop(name, default())
            )
    for default in nonpositional_defaults:
        if default in keyword_dictionary:
            arguments.append(keyword_dictionary.pop(default))
    for value in keyword_dictionary.values():
        arguments.append(value)  # append remaining unspecified arguments.
    return arguments


def get_function_call_mapping(
    *,
    function_name: str | None = None,
    arguments: Iterable[str]
    | Iterable[ast.expr]
    | Callable[
        [Iterable[ast.expr], Iterable[ast.keyword], Context], Iterable[str]
    ]
    | Callable[[Iterable[ast.expr], Iterable[ast.keyword]], Iterable[ast.expr]]
    | None = None,
    parentheses: tuple[str, str] = ("(", ")"),
    argument_delimiter: str = ", ",
    must_be_flat: bool = False,
) -> Callable[[ast.Call, Context], str]:
    def map(node: ast.Call, context: Context) -> str:
        # Reassign variables which may be written to and do _not_ use
        # `nonlocal` or similar since those writes may carry over to the next
        # call of `get_function_call_mapping`.
        function_name_: str | None = function_name
        arguments_: (
            Iterable[str]
            | Iterable[ast.expr]
            | Callable[
                [Iterable[ast.expr], Iterable[ast.keyword], Context],
                Iterable[str],
            ]
            | Callable[
                [Iterable[ast.expr], Iterable[ast.keyword]], Iterable[ast.expr]
            ]
            | None
        ) = arguments
        if must_be_flat and not isinstance(node.func, ast.Name):
            return str(node)  # inject/change as needed.
        if function_name_ is None:
            function_name_ = get_name(node.func)
        if arguments_ is None:
            arguments_ = lambda arguments, keyword_arguments: (  # noqa: E731
                organize_arguments(arguments, keyword_arguments)
            )
        if callable(arguments_):
            arguments_ = (
                arguments_(node.args, node.keywords)  # type: ignore
                if len(inspect.signature(arguments_).parameters) <= 2
                else arguments_(node.args, node.keywords, context)  # type: ignore
            )
        arguments_ = [
            argument
            if isinstance(argument, str)
            else context.translator.visit(argument)
            for argument in arguments_
        ]
        return (
            function_name_
            + parentheses[0]
            + argument_delimiter.join(arguments_)
            + parentheses[1]
        )

    return map
