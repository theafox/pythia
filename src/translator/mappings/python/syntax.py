"""This file contains general mappings for the Python programming language.

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
from typing import Callable, ClassVar, override

from translator.context import Context
from translator.mappings import BaseMapping, MappingWarning
from translator.mappings.utils import get_name, organize_arguments


class GenericStatementMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        context.line(ast.unparse(node))


class GenericExpressionMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        return ast.unparse(node)


class FunctionMapping(BaseMapping):
    decorators: Iterable[str] = []

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
                decorators = [
                    f"@{decorator.removeprefix('@')}"
                    for decorator in cls.decorators
                    if decorator
                ]
                arguments = [
                    argument.arg
                    for argument in chain(positional_arguments, arguments)
                ]
                for decorator in decorators:
                    context.line(decorator)
                context.line(f"def {name}({', '.join(arguments)}):")
                with context.indented():
                    for statement in body:
                        context.translator.visit(statement)
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for `{cls.__name__}`."
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
                context.line(f"if {context.translator.visit(conditional)}:")
                with context.indented():
                    for statement in if_body:
                        context.translator.visit(statement)
                if else_body:
                    context.line("else:")
                    with context.indented():
                        for statement in else_body:
                            context.translator.visit(statement)
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for `{cls.__name__}`."
                )


class WhileLoopMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.While(test=conditional, body=body):
                context.line(f"while {context.translator.visit(conditional)}:")
                with context.indented():
                    for statement in body:
                        context.translator.visit(statement)
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for `{cls.__name__}`."
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
                context.line(
                    f"for {target} in range({start}, {end}, {stepsize}):"
                )
                with context.indented():
                    for statement in body:
                        context.translator.visit(statement)
            case ast.For(target=target, iter=iterator, body=body):
                target = context.translator.visit(target)
                iterator = context.translator.visit(iterator)
                context.line(f"for {target} in {iterator}:")
                with context.indented():
                    for statement in body:
                        context.translator.visit(statement)
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for `{cls.__name__}`."
                )


class ReturnMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.Return(value=value):
                value = (
                    context.translator.visit(value)
                    if value is not None
                    else None
                )
                context.line(f"return {value}")
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for `{cls.__name__}`."
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
                    f" for `{cls.__name__}`."
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
                    f" for `{cls.__name__}`."
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
                    f" for `{cls.__name__}`."
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
                    f" for `{cls.__name__}`."
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
                    f" for `{cls.__name__}`."
                )


class IndexingMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.Subscript(value=target, slice=slices):
                target = context.translator.visit(target)
                slices = [
                    context.translator.visit(slicing)
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
        match node:
            case ast.Slice(lower=lower, upper=upper, step=step):
                lower, upper, step = (
                    context.translator.visit(item) if item is not None else ""
                    for item in (lower, upper, step)
                )
                return f"{lower}:{upper}:{step}"
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for `{cls.__name__}`."
                )


class CallMapping(BaseMapping):
    mappings: ClassVar[dict[str, Callable[[ast.Call, Context], str]]] = {}

    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.Call() if (name := get_name(node)) in cls.mappings:
                mapping = cls.mappings[name]
                return mapping(node, context)  # pass on `MappingError`
            case ast.Call():
                return (
                    context.translator.visit(node.func)
                    + "("
                    + ", ".join(
                        context.translator.visit(argument)
                        for argument in organize_arguments(
                            node.args, node.keywords
                        )
                    )
                    + ")"
                )
            case _:
                raise MappingWarning(
                    f"Mismatching node-type `{type(node).__name__}`"
                    f" for `{cls.__name__}`."
                )


class BinaryOperatorsMapping(BaseMapping):
    mappings: ClassVar[dict[type[ast.AST], str]] = {
        # Simple binary.
        ast.Add: "+",
        ast.Sub: "-",
        ast.Mult: "*",
        ast.Div: "/",
        ast.FloorDiv: "//",
        ast.Pow: "**",
        ast.Mod: "%",
        # Comparison.
        ast.Eq: "==",
        ast.NotEq: "!=",
        ast.Lt: "<",
        ast.LtE: "<=",
        ast.Gt: ">",
        ast.GtE: ">=",
        # Boolean.
        ast.And: "and",
        ast.Or: "or",
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
                    f" for `{cls.__name__}`."
                )


class UnaryOperatorsMapping(BaseMapping):
    mappings: ClassVar[dict[type[ast.AST], str]] = {
        ast.UAdd: "+",
        ast.USub: "-",
        ast.Not: "not",
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
                    f" for `{cls.__name__}`."
                )
