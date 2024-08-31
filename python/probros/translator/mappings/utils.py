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
    """Organize (keyword) arguments according to given defaults.

    The defaults for the positional arguments merely insert the defaults in
    case fewer arguments exist than defaults. The defaults for keyword
    arguments may only sort them according to their relative position compared
    to the other defaults (by using a simple `str`), or giving an expected
    (i) position, (ii) name, and (iii) default. Notice, since the positional
    defaults specify a minimum number of positional arguments, the keyword
    defaults may use this to specify their positions. Therefore, the order
    matters for each parameter!

    Consider the imaginary function `func(a, b, c=12, d=None)` and some usage
    of this function were the positional arguments are `["some"]` and there are
    no keyword arguments given. By using organizing parameters like
    `["text", 3.12]` for positional arguments and `[(3, "c", 12), "d"]` for
    keyword arguments, the result would be `["some", 3.12, 12]`.

    Args:
        arguments: Positional arguments to organize.
        keyword_arguments: Keyword arguments to organize.
        argument_defaults: Defaults for the positional arguments.
        keyword_argument_defaults: Defaults for the keyword arguments. In case
            only a `str` is given, simple insert it in its relative position
            according to the other defaults. In case a tuple is given, the
            arguments specifies the position (starting at 1), name, and
            default. Those are merely inserted if the position matches. This is
            important for respecting keyword arguments who may be used
            positionally.

    Returns:
        The organized arguments.
    """

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
    """Get a simple mapping for a function call.

    Args:
        function_name: The name of the function to call. In case of `None`
            extract the name dynamically.
        arguments: The arguments for the call. In case of `None` extract the
            arguments dynamically.
        parentheses: The paranthesis to use for the call.
        argument_delimiter: The delimiter seperating the arguments.
        must_be_flat: In case the original call must be flat.

    Returns:
        A function which maps nodes according to the given parameters.
    """

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
