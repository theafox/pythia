import ast
from itertools import chain
from typing import Callable, Iterable, override

from context import Context

from mappings import BaseMapping
from mappings.utils import get_function_call_mapping, get_name


class FunctionMapping(BaseMapping):
    macros: Iterable[str] = []

    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str:
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
                return str(node)
            case _:
                return str(node)


class IfMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str:
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
                return str(node)
            case _:
                return str(node)


class WhileLoopMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str:
        match node:
            case ast.While(test=conditional, body=body):
                context.line(f"while {context.translator.visit(conditional)}")
                with context.indented():
                    for statement in body:
                        context.translator.visit(statement)
                context.line("end")
                return str(node)
            case _:
                return str(node)


class ForLoopMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str:
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
                        return str(node)
                context.line(f"for {target} = {start}:{stepsize}:{end}")
                with context.indented():
                    for statement in body:
                        context.translator.visit(statement)
                context.line("end")
                return str(node)
            case _:
                return str(node)


class ContinueMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str:
        match node:
            case ast.Continue():
                context.line("continue")
                return str(node)
            case _:
                return str(node)


class BreakMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str:
        match node:
            case ast.Break():
                context.line("break")
                return str(node)
            case _:
                return str(node)


class ReturnMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str:
        match node:
            case ast.Return(value=value):
                value = context.translator.visit(value) if value else "nothing"
                context.line(f"return {value}")
                return str(node)
            case _:
                return str(node)


class AssignmentMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str:
        match node:
            case (
                ast.Assign(targets=[target, *_], value=value)
                | ast.AnnAssign(target=target, value=value)
            ) if value:
                target = context.translator.visit(target)
                value = context.translator.visit(value)
                context.line(f"{target} = {value}")
                return str(node)
            case _:
                return str(node)


class StandaloneExpressionMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str:
        match node:
            case ast.Expr(value=value):
                context.line(context.translator.visit(value))
                return str(node)
            case _:
                return str(node)


class NameMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str:
        match node:
            case ast.Name(id=name):
                return name
            case _:
                return str(node)


class ConstantMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str:
        match node:
            case ast.Constant(value=value) if isinstance(value, str):
                value = repr(value)
                value = value.replace('"', r"\"")
                value = value.replace("$", r"\$")
                return f'"{value[1:-1]}"'
            case ast.Constant(value=value):
                return str(value)
            case _:
                return str(node)


class TupleMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str:
        match node:
            case ast.Tuple(elts=[]):
                return "()"
            case ast.Tuple(elts=[element]):
                return f"({context.translator.visit(element)},)"
            case ast.Tuple(elts=[*elements]):
                evaluated = map(context.translator.visit, elements)
                return f"({", ".join(evaluated)})"
            case _:
                return str(node)


class ListMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str:
        match node:
            case ast.List(elts=[]):
                return "[]"
            case ast.List(elts=[*elements]):
                evaluated = map(context.translator.visit, elements)
                return f"[{", ".join(evaluated)}]"
            case _:
                return str(node)


class AttributeMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str:
        match node:
            case ast.Attribute(value=left, attr=right):
                return f"{context.translator.visit(left)}.{right}"
            case _:
                return str(node)


class IndexingMapping(BaseMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str:
        match node:
            case ast.Subscript(value=target, slice=index):
                target = context.translator.visit(target)
                index = context.translator.visit(index)
                return f"{target}[({index}) + 1]"
            case _:
                return str(node)


class CallMapping(BaseMapping):
    _default_mappings: dict[str, Callable[[ast.Call, Context], str]] = {
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
    mappings: dict[str, Callable[[ast.Call, Context], str]] = {}

    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str:
        # Mappings in `mappings` may override those in  `_default_mappings`.
        mappings = cls._default_mappings | cls.mappings
        match node:
            case ast.Call(func=function) if (
                name := get_name(function)
            ) in mappings:
                mapping = mappings[name]
                return mapping(node, context)  # pass on `MappingError`
            case _:
                return str(node)


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
    def map(cls, node: ast.AST, context: Context) -> str:
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
                return str(node)


class UnaryOperatorsMapping(BaseMapping):
    mappings: dict[type[ast.AST], str] = {
        ast.UAdd: "+",
        ast.USub: "-",
        ast.Not: "!",
    }

    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str:
        match node:
            case ast.UnaryOp(operand=operand, op=operator):
                operand = context.translator.visit(operand)
                operator = cls.mappings.get(type(operator))
                return f"{operator} ({operand})" if operator else str(node)
            case _:
                return str(node)
