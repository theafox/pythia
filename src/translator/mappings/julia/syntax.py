"""This file contains general mappings for the Julia programming language.

Note that additional mapping may still be required for translation. More
specific mappings requiring knowledge about the target language or framework
were omitted or generalized.

Each mapping is implemented as a class inheriting from `BaseMapping`.
Therefore, view the documentation of that class in case of changes or
additions.
"""

import ast
from collections.abc import Iterable
from itertools import chain
from typing import Callable, ClassVar, Optional, override

from translator.context import Context
from translator.mappings import BaseMapping, MappingWarning
from translator.mappings.utils import get_function_call_mapping, get_name


class FunctionMapping(BaseMapping):
    name: Optional[str] = None
    macros: Iterable[str] = []

    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.FunctionDef(
                name=name,
                args=ast.arguments(
                    posonlyargs=positional_arguments,
                    args=arguments,
                ),
                body=body,
            ):
                if cls.name is not None:
                    name = cls.name
                macros = [
                    f"@{macro.removeprefix('@')}"
                    for macro in cls.macros
                    if macro
                ]
                arguments = [
                    argument.arg
                    for argument in chain(positional_arguments, arguments)
                ]
                context.line(
                    (" ".join(macros) + " " if macros else "")
                    + f"function {name}({', '.join(arguments)})"
                )
                with context.indented():
                    for statement in body:
                        context.translator.visit(statement)
                context.line("end")
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for {cls.__name__}`."
                )


class IfMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.If(
                test=conditional,
                body=if_body,
                orelse=else_body,
            ):
                context.line(f"if {context.translator.visit(conditional)}")
                with context.indented():
                    for statement in if_body:
                        context.translator.visit(statement)
                if else_body:
                    context.line("else")
                    with context.indented():
                        for statement in else_body:
                            context.translator.visit(statement)
                context.line("end")
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for {cls.__name__}`."
                )


class WhileLoopMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.While(test=conditional, body=body):
                context.line(f"while {context.translator.visit(conditional)}")
                with context.indented():
                    for statement in body:
                        context.translator.visit(statement)
                context.line("end")
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for {cls.__name__}`."
                )


class ForLoopMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.For(
                target=target,
                iter=ast.Call(func=ast.Name(id="range"), args=arguments),
                body=body,
            ):
                target = context.translator.visit(target)
                match len(arguments):
                    case 1:
                        start = 0
                        end = context.translator.visit(arguments[0])
                        stepsize = 1
                    case 2:
                        start = context.translator.visit(arguments[0])
                        end = context.translator.visit(arguments[1])
                        stepsize = 1
                    case 3:
                        start = context.translator.visit(arguments[0])
                        end = context.translator.visit(arguments[1])
                        stepsize = context.translator.visit(arguments[2])
                    case _:
                        return
                context.line(f"for {target} = {start}:{stepsize}:({end})-1")
                with context.indented():
                    for statement in body:
                        context.translator.visit(statement)
                context.line("end")
            case ast.For(target=target, iter=iterator, body=body):
                # WARN: Arbitrary mapping of iterators to Julia comes with risk
                # Therefore, it is recommended to restrict the set of iterators
                # before attempting translation.
                target = context.translator.visit(target)
                iterator = context.translator.visit(iterator)
                context.line(f"for {target} in {iterator}")
                with context.indented():
                    for statement in body:
                        context.translator.visit(statement)
                context.line("end")
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for {cls.__name__}`."
                )


class ContinueMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.Continue():
                context.line("continue")
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for {cls.__name__}`."
                )


class BreakMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.Break():
                context.line("break")
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for {cls.__name__}`."
                )


class ReturnMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.Return(value=value):
                value = context.translator.visit(value) if value else "nothing"
                context.line(f"return {value}")
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for {cls.__name__}`."
                )


class AssignmentMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case (
                ast.Assign(targets=[target, *_], value=value)
                | ast.AnnAssign(target=target, value=value)
            ) if value:
                target = context.translator.visit(target)
                value = context.translator.visit(value)
                context.line(f"{target} = {value}")
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for {cls.__name__}`."
                )


class StandaloneExpressionMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.Expr(value=value):
                context.line(context.translator.visit(value))
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for {cls.__name__}`."
                )


class NameMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.Name(id=name):
                return name
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for {cls.__name__}`."
                )


class ConstantMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.Constant(value=value) if isinstance(value, str):
                value = repr(value)
                value = value.replace('"', r"\"")
                value = value.replace("$", r"\$")
                return f'"{value[1:-1]}"'
            case ast.Constant(value=True):
                return "true"
            case ast.Constant(value=False):
                return "false"
            case ast.Constant(value=value):
                return str(value)
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for {cls.__name__}`."
                )


class TupleMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.Tuple(elts=[]):
                return "()"
            case ast.Tuple(elts=[element]):
                return f"({context.translator.visit(element)},)"
            case ast.Tuple(elts=[*elements]):
                evaluated = map(context.translator.visit, elements)
                return f"({', '.join(evaluated)})"
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for {cls.__name__}`."
                )


class ListMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.List(elts=[]):
                return "[]"
            case ast.List(elts=[*elements]):
                evaluated = map(context.translator.visit, elements)
                return f"[{', '.join(evaluated)}]"
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for {cls.__name__}`."
                )


class AttributeMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.Attribute(value=left, attr=right):
                return f"{context.translator.visit(left)}.{right}"
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for {cls.__name__}`."
                )


class IndexingMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.Subscript(value=target, slice=slices):
                target = context.translator.visit(target)
                slices = [
                    (
                        context.translator.visit(slicing)
                        if isinstance(slicing, ast.Slice)
                        else f"({context.translator.visit(slicing)})+1"
                    )
                    for slicing in (
                        slices.elts
                        if isinstance(slices, ast.Tuple)
                        else (slices,)
                    )
                ]
                return f"{target}[{', '.join(slices)}]"
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for `{cls.__name__}`."
                )


class SlicingMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        # WARN: This currently allows translation of negative elements of
        # slices, which is not supported in Julia. Prevention of this requires
        # execution of the code to evaluate the elements. Therefore, it is
        # recommended to restrict the set of possible slicing operations before
        # attempting translation.
        match node:
            case ast.Slice(lower=lower, upper=upper, step=step):
                lower = (
                    f"({context.translator.visit(lower)})+1"
                    if lower is not None
                    else "begin"
                )
                upper = (
                    f"({context.translator.visit(upper)})+1"
                    if upper is not None
                    else "end"
                )
                step = (
                    context.translator.visit(step) if step is not None else "1"
                )
                return f"{lower}:{step}:{upper}"
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for `{cls.__name__}`."
                )


class CallMapping(BaseMapping):
    _default_mappings: ClassVar[
        dict[str, Callable[[ast.Call, Context], str]]
    ] = {
        "abs": get_function_call_mapping(must_be_flat=True),
        "max": get_function_call_mapping(must_be_flat=True),
        "min": get_function_call_mapping(must_be_flat=True),
        "sum": get_function_call_mapping(must_be_flat=True),
        "round": get_function_call_mapping(must_be_flat=True),
        # Arrays.
        "len": get_function_call_mapping(
            function_name="length", must_be_flat=True
        ),
        "sorted": get_function_call_mapping(
            function_name="sort", must_be_flat=True
        ),
        # IO.
        "print": get_function_call_mapping(
            function_name="println", must_be_flat=True
        ),
    }
    mappings: ClassVar[dict[str, Callable[[ast.Call, Context], str]]] = {}

    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        # Mappings in `mappings` may override those in  `_default_mappings`.
        mappings = cls._default_mappings | cls.mappings
        match node:
            case ast.Call() if (name := get_name(node)) in mappings:
                mapping = mappings[name]
                return mapping(node, context)  # pass on `MappingError`
            case ast.Call():
                name = get_name(node)
                raise MappingWarning(f"Unknown function `{name}` called.")
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for {cls.__name__}`."
                )


class BinaryOperatorsMapping(BaseMapping):
    mappings: ClassVar[dict[type[ast.AST], str]] = {
        # Simple binary.
        ast.Add: "+",
        ast.Sub: "-",
        ast.Mult: "*",
        ast.Div: "/",
        ast.FloorDiv: "÷",
        ast.Mod: "%",
        ast.Pow: "^",
        # Comparison.
        ast.Eq: "==",
        ast.NotEq: "!=",
        ast.Lt: "<",
        ast.LtE: "<=",
        ast.Gt: ">",
        ast.GtE: ">=",
        # Boolean.
        ast.And: "&&",
        ast.Or: "||",
    }

    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.BinOp(left=left, op=operator, right=right):
                left = context.translator.visit(left)
                operator = cls.mappings.get(type(operator))
                right = context.translator.visit(right)
                return (
                    f"({left}) {operator} ({right})" if operator else str(node)
                )
            case ast.Compare(left=left, ops=operators, comparators=rights):
                left = context.translator.visit(left)
                operators = (
                    mapped
                    if (mapped := cls.mappings.get(type(operator)))
                    else node
                    for operator in operators
                )
                rights = map(context.translator.visit, rights)
                return f"({left}) " + " ".join(
                    [
                        f"{operator} ({right})"
                        for operator, right in zip(operators, rights)
                    ]
                )
            case ast.BoolOp(op=operator, values=values):
                operator = cls.mappings.get(type(operator))
                values = map(context.translator.visit, values)
                return (
                    f" {operator} ".join(f"({value})" for value in values)
                    if operator
                    else str(node)
                )
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for {cls.__name__}`."
                )


class UnaryOperatorsMapping(BaseMapping):
    mappings: ClassVar[dict[type[ast.AST], str]] = {
        ast.UAdd: "+",
        ast.USub: "-",
        ast.Not: "!",
    }

    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.UnaryOp(operand=operand, op=operator):
                operand = context.translator.visit(operand)
                operator = cls.mappings.get(type(operator))
                return f"{operator} ({operand})" if operator else str(node)
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for {cls.__name__}`."
                )
