import ast
from dataclasses import KW_ONLY, dataclass
from itertools import chain
from typing import Callable, Iterable, override

from context import Context

from .. import BaseMapping
from ..base import MappingError
from ..utils import get_name


class FunctionMapping(BaseMapping):
    macros: Iterable[str] = []

    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        match node:
            case ast.FunctionDef(
                name=name,
                args=ast.arguments(
                    posonlyargs=positional_arguments,
                    args=arguments,
                ),
                body=body,
            ):
                macros = [
                    f"@{macro.removeprefix("@")}"
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
                return node
            case _:
                return node


class IfMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
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
                return node
            case _:
                return node


class WhileLoopMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        match node:
            case ast.While(test=conditional, body=body):
                context.line(f"while {context.translator.visit(conditional)}")
                with context.indented():
                    for statement in body:
                        context.translator.visit(statement)
                context.line("end")
                return node
            case _:
                return node


class ForLoopMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
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
                        return node
                context.line(f"for {target} = {start}:{stepsize}:{end}")
                with context.indented():
                    for statement in body:
                        context.translator.visit(statement)
                context.line("end")
                return node
            case _:
                return node


class ContinueMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        match node:
            case ast.Continue():
                context.line("continue")
                return node
            case _:
                return node


class BreakMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        match node:
            case ast.Break():
                context.line("break")
                return node
            case _:
                return node


class ReturnMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        match node:
            case ast.Return(value=value):
                value = context.translator.visit(value) if value else "nothing"
                context.line(f"return {value}")
                return node
            case _:
                return node


class AssignmentMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        match node:
            case (
                ast.Assign(targets=[target, *_], value=value)
                | ast.AnnAssign(target=target, value=value)
            ) if value:
                target = context.translator.visit(target)
                value = context.translator.visit(value)
                context.line(f"{target} = {value}")
                return node
            case _:
                return node


class StandaloneExpressionMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        match node:
            case ast.Expr(value=value):
                context.line(str(context.translator.visit(value)))
                return node
            case _:
                return node


class NameMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        match node:
            case ast.Name(id=name):
                return name
            case _:
                return node


class ConstantMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        match node:
            case ast.Constant(value=value) if isinstance(value, str):
                value = repr(value)
                value = value.replace('"', r"\"")
                value = value.replace("$", r"\$")
                return f'"{value[1:-1]}"'
            case ast.Constant(value=value):
                return str(value)
            case _:
                return node


class TupleMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        match node:
            case ast.Tuple(elts=[]):
                return "()"
            case ast.Tuple(elts=[element]):
                return f"({context.translator.visit(element)},)"
            case ast.Tuple(elts=[*elements]):
                evaluated = map(context.translator.visit, elements)
                return f"({", ".join(map(str, evaluated))})"
            case _:
                return node


class ListMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        match node:
            case ast.List(elts=[]):
                return "[]"
            case ast.List(elts=[*elements]):
                evaluated = map(context.translator.visit, elements)
                return f"[{", ".join(map(str, evaluated))}]"
            case _:
                return node


class AttributeMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        match node:
            case ast.Attribute(value=left, attr=right):
                return f"{context.translator.visit(left)}.{right}"
            case _:
                return node


class IndexingMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        match node:
            case ast.Subscript(value=target, slice=index):
                target = context.translator.visit(target)
                index = context.translator.visit(index)
                return f"{target}[({index}) + 1]"
            case _:
                return node


class CallMapping(BaseMapping):
    @dataclass(frozen=True)
    class Mapping:
        frm: str
        to: str
        _: KW_ONLY  # continue with keyword-only arguments
        must_be_flat: bool = False
        check_arguments: Callable[[Iterable[ast.expr]], bool | str] = (
            lambda _: True
        )
        normalize_arguments: Callable[
            [Iterable[ast.expr], Iterable[ast.keyword], Context],
            Iterable[ast.expr],
        ] = lambda arguments, keywords, _: list(arguments) + [
            keyword.value for keyword in keywords
        ]
        map_arguments: Callable[
            [Iterable[ast.expr], Context], Iterable[str]
        ] = lambda arguments, context: map(
            str, map(context.translator.visit, arguments)
        )

    _default_mappings: Iterable[Mapping] = {
        # Maths.
        Mapping("abs", "abs", must_be_flat=True),
        Mapping("max", "max", must_be_flat=True),
        Mapping("min", "min", must_be_flat=True),
        Mapping("sum", "sum", must_be_flat=True),
        Mapping("round", "round", must_be_flat=True),
        # Arrays.
        Mapping("len", "length", must_be_flat=True),
        Mapping("sorted", "sort", must_be_flat=True),
        # IO.
        Mapping("print", "println", must_be_flat=True),
    }

    # In case multiple mappings are defined for the same function, the most
    # recent the iterator extracts is used. Therefore, this may be used to
    # override default mappings such as `abs`.
    mappings: Iterable[Mapping] = {}

    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        # Convert to native mapping-data-structure for easier key lookup.
        # Additionally, this eliminates any duplicate entries, using the last
        # one found.
        mappings = {
            mapping.frm: mapping
            for mapping in chain(cls._default_mappings, cls.mappings)
        }
        match node:
            case ast.Call(
                func=function,
                args=arguments,
                keywords=keyword_arguments,
            ) if (name := get_name(function)) in mappings and not (
                isinstance(function, ast.Attribute)
                and mappings[name].must_be_flat
            ):
                arguments = mappings[name].normalize_arguments(
                    arguments, keyword_arguments, context
                )
                if (
                    message := mappings[name].check_arguments(arguments)
                ) is not True:
                    raise (
                        MappingError(message)
                        if message is not False
                        else MappingError()
                    )

                arguments = mappings[name].map_arguments(arguments, context)
                name = mappings[name].to
                return f"{name}({", ".join(arguments)})"
            case _:
                return node


class BinaryOperatorsMapping(BaseMapping):
    mappings: dict[type[ast.AST], str] = {
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
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        match node:
            case ast.BinOp(left=left, op=operator, right=right):
                left = context.translator.visit(left)
                operator = cls.mappings.get(type(operator))
                right = context.translator.visit(right)
                return f"({left}) {operator} ({right})" if operator else node
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
                    else node
                )
            case _:
                return node


class UnaryOperatorsMapping(BaseMapping):
    mappings: dict[type[ast.AST], str] = {
        ast.UAdd: "+",
        ast.USub: "-",
        ast.Not: "!",
    }

    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        match node:
            case ast.UnaryOp(operand=operand, op=operator):
                operand = context.translator.visit(operand)
                operator = cls.mappings.get(type(operator))
                return f"{operator} ({operand})" if operator else node
            case _:
                return node
