import ast
from itertools import chain
from typing import override

from context import Context

from .. import BaseMapping
from ..utils import get_name


class FunctionMapping(BaseMapping):
    function_macro: str | None = None

    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        if not isinstance(node, ast.FunctionDef):
            return node
        name = node.name
        arguments = [
            argument.arg
            for argument in chain(node.args.posonlyargs, node.args.args)
        ]
        context.line(
            (f"{cls.function_macro} " if cls.function_macro else "")
            + f"function {name}({', '.join(arguments)})"
        )
        with context.indented():
            for statement in node.body:
                context.translator.visit(statement)
        context.line("end")
        return node


class IfMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        if not isinstance(node, ast.If):
            return node
        context.line(f"if {context.translator.visit(node.test)}")
        with context.indented():
            for statement in node.body:
                context.translator.visit(statement)
        if node.orelse:
            context.line("else")
            with context.indented():
                for statement in node.orelse:
                    context.translator.visit(statement)
        context.line("end")
        return node


class WhileLoopMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        if not isinstance(node, ast.While):
            return node
        context.line(f"while {context.translator.visit(node.test)}")
        with context.indented():
            for statement in node.body:
                context.translator.visit(statement)
        context.line("end")
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
        if not isinstance(node, ast.Continue):
            return node
        context.line("continue")
        return node


class BreakMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        if not isinstance(node, ast.Break):
            return node
        context.line("break")
        return node


class ReturnMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        if not isinstance(node, ast.Return):
            return node
        value = context.translator.visit(node.value) if node.value else "nothing"
        context.line(f"return {value}")
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


class NameMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        return node.id if isinstance(node, ast.Name) else node


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


class IndexingMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        if not isinstance(node, ast.Subscript):
            return node
        target = context.translator.visit(node.value)
        index = context.translator.visit(node.slice)
        return f"{target}[({index}) + 1]"


class CallMapping(BaseMapping):
    # TODO: translate specific arguments properly
    mappings: dict[str, str] = {
        "len": "length",
        "abs": "abs",
        "sum": "sum",
        "max": "maximum",
        "min": "minimum",
        "sorted": "sort",
        "round": "round",
        "print": "println",
    }

    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        match node:
            case ast.Call(
                func=function,
                args=arguments,
            ) if (
                name := get_name(function, flat_name_only=True)
            ) in cls.mappings.keys():
                name = cls.mappings[name]
                arguments = map(context.translator.visit, arguments)
                return f"{name}({", ".join(map(str, arguments))})"
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
        if not isinstance(node, ast.UnaryOp):
            return node
        operand = context.translator.visit(node.operand)
        operator = cls.mappings.get(type(node.op))
        if not operator:
            return node
        return f"{operator} ({operand})"
