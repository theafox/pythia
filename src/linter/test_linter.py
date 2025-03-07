"""This contains tests for the probabilistic programming linter using `pytest`.

The tests validate the functionality of the linter to ensure proper
functionality, i.e. it correctly identifies and flags invalid code patterns in
probabilistic programs. Each test case checks specific rules. They all parse
the code as a string and match the resulting diagnostics against whats
expected.

This test-file and the test-cases are intended to be used with `pytest`. Its
fixture feature is used to parse a default probabilistic program to each
test-case.

The names of the test-cases generally follow the following pattern:
```
    test_(warned|prohibited|restrict(ed)?)_<the rule name>_<any sub-test-cases>
```

Fixtures:
    - default_linter: A `pytest` fixture that provides a default instance of
        the probabilistic program linter.
"""

import pytest

from linter import (
    Linter,
    Severity,
    default_probabilistic_program_linter,
    rules,
)


@pytest.fixture
def default_linter() -> Linter:
    return default_probabilistic_program_linter()


class TestEntryPointRecognition:
    class TestUnrecognizedDecoratorWarning:
        @staticmethod
        def test_unrecognized_decorator_addition(
            default_linter: Linter,
        ) -> None:
            code = """
@1 + 1
def test_unrecognized_decorator_addition():
    pass
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.WARNING

        @staticmethod
        def test_unrecognized_decorator_string(default_linter: Linter) -> None:
            code = """
@"hello decorator!"
def test_unrecognized_decorator_string():
    pass
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.WARNING

        @staticmethod
        def test_unrecognized_decorator_matching_string(
            default_linter: Linter,
        ) -> None:
            code = """
@"probabilistic_program"
def test_unrecognized_decorator_matching_string():
    pass
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.WARNING

    class TestInvalidEntryPoints:
        @staticmethod
        def test_valid_entry_point_positional_only_arguments(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_valid_entry_point_positional_only_arguments(a, b, /, c):
    return a + b + c
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_invalid_entry_point_keyword_argument(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_invalid_entry_point_keyword_argument(data=None):
    return data
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR

        @staticmethod
        def test_invalid_entry_point_keyword_only_argument(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_invalid_entry_point_keyword_only_argument(a, *args, b):
    return a * b
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR

        @staticmethod
        def test_invalid_entry_point_catch_argument(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_invalid_entry_point_catch_argument(data, *args):
    return data
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR

        @staticmethod
        def test_invalid_entry_point_catch_keyword_argument(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_invalid_entry_point_catch_keyword_argument(data, **kwargs):
    return data
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR

        @staticmethod
        def test_warned_entry_point_typing(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_warned_entry_point_typing(data: list[int]):
    return data
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.WARNING

        @staticmethod
        def test_warned_entry_point_typed_keyword_argument(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_invalid_entry_point_typed_keyword_argument(data: list[int] = []):
    return data
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 2
            severities = [diagnostic.severity for diagnostic in diagnostics]
            assert Severity.ERROR in severities
            assert Severity.WARNING in severities

    class TestUncheckedDefinitions:
        @staticmethod
        def test_unchecked_code_decorator_definition(
            default_linter: Linter,
        ) -> None:
            code = """
def test_unchecked_code_decorator_definition(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        func(*args, **kwargs)

    return wrapper
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_unchecked_code_different_decorator_usage(
            default_linter: Linter,
        ) -> None:
            code = """
@test_unchecked_code_decorator_definition
def test_unchecked_code_different_decorator_usage():
    VAR = f"This should {'allow'} anything!"

    def test_unchecked_code_different_decorator_usage_nested_function(arg):
        return f"{arg=} including f-strings"

    VAR += "\\nand nested functions"
    return test_unchecked_code_different_decorator_usage_nested_function(VAR)
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

    class TestNestedProbabilisticProgramDefinition:
        @staticmethod
        def test_valid_probabilistic_program(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_valid_probabilistic_program(data):
    probability = sample("p", Uniform(0, 1))
    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress("flip", i),
            Bernoulli(probability),
        )
    return probability
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_invalid_probabilistic_program(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_invalid_probabilistic_program(data):
    probability = sample("p", Uniform(0, 1))
    for i in range(0, len(data)):
        address = f"flip[{i}]"
        observe(data[i], address, Bernoulli(probability))
    return probability
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 2
            assert all(
                diagnostic.severity == Severity.ERROR
                for diagnostic in diagnostics
            )
            messages = [diagnostic.message for diagnostic in diagnostics]
            assert rules.NoFstringRule.message in messages
            assert rules.RestrictObserveCallStructureRule.message in messages

        @staticmethod
        def test_valid_probabilistic_class_method(
            default_linter: Linter,
        ) -> None:
            code = """
class TestValidProbabilisticClassMethodOuter:
    @probabilistic_program
    def test_valid_probabilistic_class_method(self):
        count = 0
        for i in range(0, self.length):
            probability = sample(
                IndexedAddress("this", i),
                Uniform(0, 1),
            )
            if probability < 0.1:
                return None
            else:
                count = count + 1
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_invalid_probabilistic_class_method(
            default_linter: Linter,
        ) -> None:
            code = """
class TestProhibitedFstringInClassMethod:
    @probabilistic_program
    def test_invalid_probabilistic_class_method(self):
        count = 0
        for i in range(0, self.length):
            address = f"this[{i}]"
            probability = sample(address, Uniform(0, 1))
            if probability < 0.1:
                return None
            else:
                count = count + 1
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 2
            assert all(
                diagnostic.severity == Severity.ERROR
                for diagnostic in diagnostics
            )
            messages = [diagnostic.message for diagnostic in diagnostics]
            assert rules.NoFstringRule.message in messages
            assert rules.RestrictSampleCallStructureRule.message in messages

        @staticmethod
        def test_valid_probabilistic_program_in_function(
            default_linter: Linter,
        ) -> None:
            code = """
def test_valid_probabilistic_program_in_function_outer():
    @probabilistic_program
    def test_valid_probabilistic_program_in_function(data):
        for i in range(0, len(data)):
            observe(
                data[i],
                IndexedAddress("data", i),
                Poisson(0.7),
            )
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_invalid_probabilistic_program_in_function(
            default_linter: Linter,
        ) -> None:
            code = """
def test_prohibited_fstring_in_function_outer():
    @probabilistic_program
    def test_invalid_probabilistic_program_in_function(data):
        for i in range(0, len(data)):
            address = f"data[{i}]"
            observe(
                data[i],
                address,
                Poisson(0.2),
            )
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 2
            assert all(
                diagnostic.severity == Severity.ERROR
                for diagnostic in diagnostics
            )
            messages = [diagnostic.message for diagnostic in diagnostics]
            assert rules.NoFstringRule.message in messages
            assert rules.RestrictObserveCallStructureRule.message in messages


class TestStatementLinting:
    class TestProhibitedNestedDefinitionsAndImports:
        @staticmethod
        def test_prohibited_nested_function(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_nested_function(data):
    @probabilistic_program
    def test_prohibited_nested_function_nested():
        probability = sample("p", Uniform(0, 1))
        for i in range(0, len(data)):
            observe(
                data[i],
                f"flip[{i}]",
                Bernoulli(probability),
            )
        return probability

    return test_prohibited_nested_function_nested()
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message == rules.NoNestedFunctionsRule.message
            )

        @staticmethod
        def test_prohibited_nested_class(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_nested_class():
    class TestProhibitedNestedClassNested:
        pi = 3

    return TestProhibitedNestedClassNested.pi
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert diagnostics[0].message == rules.NoNestedClassesRule.message

        @staticmethod
        def test_prohibited_import(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_import(degrees):
    import math

    return math.radians(degrees)
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert diagnostics[0].message == rules.NoImportRule.message

        @staticmethod
        def test_prohibited_import_from(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_import_from():
    from random import randint

    return randint(0, 10)
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert diagnostics[0].message == rules.NoImportRule.message

        @staticmethod
        def test_prohibited_gloabl(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_gloabl():
    global x
    x = 23
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.NoGlobalOrNonlocalDeclarationRule.message
            )

        @staticmethod
        def test_prohibited_nonlocal(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_nonlocal():
    nonlocal x
    x = 23
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.NoGlobalOrNonlocalDeclarationRule.message
            )

    class TestRestrictedVariableManipulation:
        @staticmethod
        def test_prohibited_delete(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_delete(data):
    sum = 0
    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress("data", i),
            Uniform(0, 1),
        )
        sum = sum + data[i]
    del sum
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message == rules.NoDeleteStatementRule.message
            )

        @staticmethod
        def test_prohibited_type_aliasing(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_type_aliasing():
    type Probabilities = list[Beta]
    probability: Probabilities = []
    for i in range(0, 5):
        probability = probability + Beta(0.1, 0.5)
    return probability
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 2
            assert any(
                diagnostic.severity == Severity.ERROR
                and diagnostic.message == rules.NoTypeAliasRule.message
                for diagnostic in diagnostics
            )
            assert any(
                diagnostic.severity == Severity.WARNING
                and diagnostic.message == rules.WarnAnnotatedAssignRule.message
                for diagnostic in diagnostics
            )

        @staticmethod
        def test_allowed_array_assign(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_allowed_array_assign(data):
    details = list()
    details[0] = data
    details[1] = sum(data)
    details[2] = len(data)
    details[3] = details[1] / details[2]
    return details
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_prohibited_deconstructor(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_deconstructor(data):
    mean, stddev = 2, 0.3
    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress("data", i),
            Normal(mean, stddev),
        )
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert diagnostics[0].message == rules.NoDeconstructorRule.message

        @staticmethod
        def test_prohibited_augmented_assign_addition(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_prohibited_augmented_assign_addition(probability):
    probability += 0.01
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message == rules.NoAugmentedAssignRule.message
            )

        @staticmethod
        def test_prohibited_augmented_assign_and_bitwise(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_prohibited_augmented_assign_and_bitwise(probability):
    probability ^= 0b1010
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message == rules.NoAugmentedAssignRule.message
            )

        @staticmethod
        def test_prohibited_augmented_assign_division(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_prohibited_augmented_assign_division(probability):
    probability /= 2
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message == rules.NoAugmentedAssignRule.message
            )

        @staticmethod
        def test_prohibited_augmented_assign_power(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_prohibited_augmented_assign_power(probability):
    probability **= 2
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message == rules.NoAugmentedAssignRule.message
            )

        @staticmethod
        def test_warned_annotated_assign_int(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_warned_annotated_assign_int(a):
    b: int = a
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.WARNING
            assert (
                diagnostics[0].message == rules.WarnAnnotatedAssignRule.message
            )

        @staticmethod
        def test_prohibited_chained_assign(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_chained_assign(data):
    x = y = data
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message == rules.NoChainedAssignmentRule.message
            )

        @staticmethod
        def test_prohibited_attribute_assign(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_attribute_assign(data):
    data.sum = sum(data)
    return data.sum
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message == rules.NoAttributeAssignRule.message
            )

    class TestRestrictedControlFlowStructures:
        @staticmethod
        def test_prohibited_standalone_expression_allowed_observe(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_prohibited_standalone_expression_allowed_observe():
    observe(
        12,
        "standalone_observe_call",
        Uniform(0, 1),
    )
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_prohibited_standalone_expression_allowed_factor(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_prohibited_standalone_expression_allowed_factor():
    factor(0.0124)
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_prohibited_standalone_expression_function_call(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_prohibited_standalone_expression_function_call(n):
    initialize_context()
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.NoStandaloneExpressionRule.message
            )

        @staticmethod
        def test_prohibited_standalone_expression_calculations(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_prohibited_standalone_expression_calculations(n):
    1 + 2**3 / 4 // 5
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.NoStandaloneExpressionRule.message
            )

        @staticmethod
        def test_restricted_for_iterable(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_restricted_for_iterable(data):
    for point in data:
        if (point.x < 0 or point.x > 100) and (point.y < 0 or point.y > 100):
            return "outside X and Y"
        elif point.x < 0 or point.x > 100:
            return "outside X"
        elif point.y < 0 or point.y > 100:
            return "outside Y"
        else:
            return "inside X and Y"
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictForLoopIteratorRule.message
            )

        @staticmethod
        def test_restricted_for_iterable_constant(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_for_iterable_constant(data):
    step = 0
    for _ in "this shouldn't work either!":
        observe(data[step], "hi!", Uniform(0, 1))
        step += 1
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictForLoopIteratorRule.message
            )

        @staticmethod
        def test_prohibited_for_else(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_for_else(data):
    for i in range(0, 10):
        continue
    else:
        myvar = "hello"
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert diagnostics[0].message == rules.NoForElseRule.message

        @staticmethod
        def test_prohibited_while_else(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_while_else(data):
    while False:
        continue
    else:
        myvar = "hello"
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert diagnostics[0].message == rules.NoWhileElseRule.message

        @staticmethod
        def test_prohibited_with_file(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_with_file(filepath):
    with open(filepath) as file:
        data = file.readall()
    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress("data", i),
            Uniform(0, 1),
        )
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert diagnostics[0].message == rules.NoWithStatementRule.message

        @staticmethod
        def test_prohibited_with_variables(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_with_variables(generator):
    with generator() as data:
        for i in range(0, len(data)):
            observe(
                data[i],
                IndexedAddress("data", i),
                Uniform(0, 1),
            )
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert diagnostics[0].message == rules.NoWithStatementRule.message

        @staticmethod
        def test_prohibited_match(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_match(data):
    match data:
        case []:
            return False
        case _:
            return True
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert diagnostics[0].message == rules.NoMatchRule.message

        @staticmethod
        def test_prohibited_asynchronous_function_definition(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_prohibited_asynchronous_function_definition(data):
    async def test_prohibited_asynchronous_function_definition_nested():
        return None
            """
            default_linter.extensive_diagnosis = True
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 2
            assert all(
                diagnostic.severity == Severity.ERROR
                for diagnostic in diagnostics
            )
            messages = [diagnostic.message for diagnostic in diagnostics]
            assert rules.NoAsynchronousStatementRule.message in messages
            assert rules.NoNestedFunctionsRule.message in messages

        @staticmethod
        def test_prohibited_asynchronous_for(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_asynchronous_for(data):
    probability = Gamma(0.2, 0.9)
    if probability < 0.5:
        return False
    else:
        async for i in range(0, len(data)):
            observe(
                data[i],
                IndexedAddress("data", i),
                Gamma(0.2, 0.9),
            )
        return True
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.NoAsynchronousStatementRule.message
            )

        @staticmethod
        def test_prohibited_asynchronous_with(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_asynchronous_with(path):
    async with open(path, "r"):
        return None
            """
            default_linter.extensive_diagnosis = True
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 2
            assert all(
                diagnostic.severity == Severity.ERROR
                for diagnostic in diagnostics
            )
            messages = [diagnostic.message for diagnostic in diagnostics]
            assert rules.NoAsynchronousStatementRule.message in messages
            assert rules.NoWithStatementRule.message in messages

        @staticmethod
        def test_prohibited_pass(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_pass(data):
    pass
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert diagnostics[0].message == rules.NoPassRule.message

        @staticmethod
        def test_valid_return(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_valid_return(data):
    return None
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_prohibited_empty_return(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_empty_return(data):
    return
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert diagnostics[0].message == rules.NoEmptyReturnRule.message

    class TestRestrictedExceptionHandling:
        @staticmethod
        def test_prohibited_raise(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_raise(data):
    raise RuntimeError("forbidden!")
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert diagnostics[0].message == rules.NoRaiseExceptionRule.message

        @staticmethod
        def test_prohibited_try_except(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_try_except(data):
    try:
        return None
    except:
        return None
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert diagnostics[0].message == rules.NoTryExceptRule.message

        @staticmethod
        def test_prohibited_assert(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_assert(data):
    assert True
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert diagnostics[0].message == rules.NoAssertRule.message


class TestExpressionLinting:
    class TestRestrictedOperators:
        @staticmethod
        def test_restricted_unary_operator_bitwise(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_unary_operator_bitwise(n):
    return ~n
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictUnaryOperatorsRule.message
            )

        @staticmethod
        def test_restricted_binary_operators_shift(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_binary_operators_shift(n):
    return 1 << n
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictBinaryOperatorsRule.message
            )

        @staticmethod
        def test_restricted_binary_operators_bitwise(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_binary_operators_bitwise(a, b, c, d):
    result = a & b
    result = result | c
    result = result ^ d
    return result
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 3
            assert all(
                diagnostic.severity == Severity.ERROR
                for diagnostic in diagnostics
            )
            assert all(
                diagnostic.message == rules.RestrictBinaryOperatorsRule.message
                for diagnostic in diagnostics
            )

        @staticmethod
        def test_restricted_comparison_operators(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_comparison_operators(a, b, c, d, e, f, g):
    result = a == b
    result = result != c
    result = result < d
    result = result <= e
    result = result > f
    result = result >= g
    return result
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_restricted_comparison_operators_is(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_comparison_operators_is(a, b):
    return a is b
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictComparisonOperatorsRule.message
            )

        @staticmethod
        def test_restricted_comparison_operators_is_not(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_comparison_operators_is_not(a, b):
    return a is not b
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictComparisonOperatorsRule.message
            )

        @staticmethod
        def test_restricted_comparison_operators_in(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_comparison_operators_in(a, b):
    return a in b
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictComparisonOperatorsRule.message
            )

        @staticmethod
        def test_restricted_comparison_operators_not_in(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_comparison_operators_not_in(a, b):
    return a not in b
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictComparisonOperatorsRule.message
            )

        @staticmethod
        def test_restricted_comparison_operators_multiple(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_comparison_operators_multiple(a, b, c):
    return a < b <= c
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictComparisonOperatorsRule.message
            )

    class TestProhibitedInlineStatements:
        @staticmethod
        def test_prohibited_walrus(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_walrus(data):
    if (length := len(data)) > 10:
        for i in range(0, length):
            observe(
                data[i],
                IndexedAddress("data", i),
                Uniform(0, 1),
            )
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert diagnostics[0].message == rules.NoWalrusOperatorRule.message

        @staticmethod
        def test_prohibited_lambda(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_lambda(data):
    data = filter(lambda point: point >= 0, data)
    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress("data", i),
            Gamma(0.1, 0.5),
        )
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert diagnostics[0].message == rules.NoLambdaRule.message

        @staticmethod
        def test_prohibited_inline_if(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_inline_if(probability):
    probability = 0 if probability < 0 else probability
    i = 0
    while True:
        result = sample(
            IndexedAddress("data", i),
            Bernoulli(probability),
        )
        if result == 1:
            break
        i = i + 1
    return i
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert diagnostics[0].message == rules.NoInlineIfRule.message

    class TestRestrictedDataStructures:
        @staticmethod
        def test_prohibited_dictionary(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_dictionary(data):
    details = {
        "data": (data := data),
        "length": (length := data),
        "sum": (zum := data),
        "mean": zum / length,
    }

    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress("data", i),
            Uniform(0, 1),
        )

    details["remark"] = "hello world!"
    return details
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert diagnostics[0].message == rules.NoDictionaryRule.message

        @staticmethod
        def test_prohibited_set(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_set(data):
    reduced = set()
    for i in range(0, len(data)):
        reduced.add(data[i])
    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress("data", i),
            Uniform(0, 1),
        )
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 2
            assert all(
                diagnostic.severity == Severity.ERROR
                for diagnostic in diagnostics
            )
            messages = [diagnostic.message for diagnostic in diagnostics]
            assert rules.NoSetRule.message in messages
            assert rules.NoStandaloneExpressionRule.message in messages

        @staticmethod
        def test_prohibited_comprehension_list(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_comprehension_list():
    return [2**n for n in range(10)]
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.NoComprehensionAndGeneratorRule.message
            )

        @staticmethod
        def test_prohibited_comprehension_set(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_comprehension_set():
    return {2**n for n in range(10)}
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.NoComprehensionAndGeneratorRule.message
            )

        @staticmethod
        def test_prohibited_comprehension_dictionary(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_prohibited_comprehension_dictionary():
    return {n: 2**n for n in range(10)}
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.NoComprehensionAndGeneratorRule.message
            )

        @staticmethod
        def test_prohibited_generator(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_generator():
    return sum(2**n for n in range(10))
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.NoComprehensionAndGeneratorRule.message
            )

    class TestRestrictedControlFlowManipulation:
        @staticmethod
        def test_prohibited_asynchronous_await(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_asynchronous_await(data):
    probabilities = await test_prohibited_asynchronous_generator()
    for i in range(0, len(probabilities)):
        if probabilities[i] > 0.9:
            return True
    return False
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.NoAsynchronousExpressionRule.message
            )

        @staticmethod
        def test_prohibited_asynchronous_generator(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_prohibited_asynchronous_generator():
    return [Normal(n, n * 0.1) async for n in range(10)]
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 2
            assert all(
                diagnostic.severity == Severity.ERROR
                for diagnostic in diagnostics
            )
            messages = [diagnostic.message for diagnostic in diagnostics]
            assert rules.NoAsynchronousExpressionRule.message in messages
            assert rules.NoComprehensionAndGeneratorRule.message in messages

        @staticmethod
        def test_prohibited_yield(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_yield(data):
    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress("data", i),
            Uniform(0, 1),
        )
        yield data[i]
            """
            default_linter.extensive_diagnosis = True
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 2
            assert all(
                diagnostic.severity == Severity.ERROR
                for diagnostic in diagnostics
            )
            messages = [diagnostic.message for diagnostic in diagnostics]
            assert rules.NoYieldRule.message in messages
            assert rules.NoStandaloneExpressionRule.message in messages

        @staticmethod
        def test_prohibited_yield_from(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_yield_from(data):
    yield from test_prohibited_yield(data)
            """
            default_linter.extensive_diagnosis = True
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 2
            assert all(
                diagnostic.severity == Severity.ERROR
                for diagnostic in diagnostics
            )
            messages = [diagnostic.message for diagnostic in diagnostics]
            assert rules.NoYieldRule.message in messages
            assert rules.NoStandaloneExpressionRule.message in messages

    class TestRestrictedSyntax:
        @staticmethod
        def test_prohibited_fstring(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_fstring():
    return f"prohibited {'f-string'}!"
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert diagnostics[0].message == rules.NoFstringRule.message

        @staticmethod
        def test_prohibited_starred(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_prohibited_starred(data):
    zum = sum(*data)
    for i in range(0, len(data)):
        data[i] = data[i] / zum
    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress("data", i),
            Dirac(0.25),
        )
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert diagnostics[0].message == rules.NoStarredRule.message

        @staticmethod
        def test_prohibited_type_parameters_alias(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_prohibited_type_parameters_alias(data):
    type Alias[*Ts] = tuple[*Ts]
            """
            default_linter.extensive_diagnosis = True
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 3
            assert all(
                diagnostic.severity == Severity.ERROR
                for diagnostic in diagnostics
            )
            messages = [diagnostic.message for diagnostic in diagnostics]
            assert rules.NoTypeAliasRule.message in messages
            assert rules.NoStarredRule.message in messages
            assert rules.NoTypeParameterRule.message in messages

        @staticmethod
        def test_prohibited_type_parameters_function(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_prohibited_type_parameters_function(data):
    def first[T](l: list[T]) -> T:
        return l[0]
            """
            default_linter.extensive_diagnosis = True
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 2
            assert all(
                diagnostic.severity == Severity.ERROR
                for diagnostic in diagnostics
            )
            messages = [diagnostic.message for diagnostic in diagnostics]
            assert rules.NoNestedFunctionsRule.message in messages
            assert rules.NoTypeParameterRule.message in messages


class TestPythiaSpecificLinting:
    class TestRestrictedSample:
        @staticmethod
        def test_restricted_sample_structure(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_restricted_sample_structure(data):
    return sample("p", Dirac(True))
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_restricted_sample_structure_incorrect_address_number(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_sample_structure_incorrect_address_number(data):
    return sample(123, Dirac(True))
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictSampleCallStructureRule.message
            )

        @staticmethod
        def test_restricted_sample_structure_missing_argument(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_sample_structure_missing_argument(data):
    return sample("p")
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictSampleCallStructureRule.message
            )

        @staticmethod
        def test_restricted_sample_structure_incorrect_keyword_argument(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_sample_structure_incorrect_keyword_argument(data):
    return sample("p", distribution=Uniform(0, 1))
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictSampleCallStructureRule.message
            )

    class TestRestrictedObserve:
        @staticmethod
        def test_restricted_observe_call_address_number(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_observe_call_address_number(data):
    probability = sample("p", Uniform(0, 1))
    for i in range(0, len(data)):
        observe(data[i], 123, Bernoulli(probability))
    return probability
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictObserveCallStructureRule.message
            )

        @staticmethod
        def test_restricted_observe_call_address_variable(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_observe_call_address_variable(data):
    for i in range(0, len(data)):
        address = IndexedAddress("data", i)
        observe(
            data[i],
            address,
            Poisson(0.2),
        )
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictObserveCallStructureRule.message
            )

        @staticmethod
        def test_restricted_observe_structure_two_keyword_arguments(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restrict_observe_structure_two_keyword_arguments(data):
    for i in range(0, len(data)):
        observe(
            data[i],
            distribution=Poisson(0.2),
            address=IndexedAddress("data", i),
        )
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_restricted_observe_structure_one_keyword_argument(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restrict_observe_structure_one_keyword_argument(data):
    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress("data", i),
            distribution=Poisson(0.2),
        )
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_restricted_observe_structure_incorrect_ordering(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restrict_observe_structure_incorrect_ordering(data):
    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress("data", i),
            address=IndexedAddress("data", i),
        )
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictObserveCallStructureRule.message
            )

        @staticmethod
        def test_restricted_observe_structure_missing_positional(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restrict_observe_structure_missing_positional(data):
    for i in range(0, len(data)):
        observe(
            value=data[i],
            distribution=Poisson(0.2),
            address=IndexedAddress("data", i),
        )
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictObserveCallStructureRule.message
            )

    class TestRestrictedFactor:
        @staticmethod
        def test_restricted_factor_valid_keyword(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_factor_valid_keyword():
    factor(0.001, address="data")
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_restricted_factor_valid_indexed_address(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_factor_valid_indexed_address():
    factor(0.001, IndexedAddress("data", 0))
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_restricted_factor_missing_expression(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_factor_missing_expression():
    factor()
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictFactorCallStructureRule.message
            )

        @staticmethod
        def test_restricted_factor_additional_argument(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_factor_additional_argument():
    factor(0.123, "address", Beta(0.1, 0.2))
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictFactorCallStructureRule.message
            )

    class TestRestrictedAddresses:
        @staticmethod
        def test_restricted_observe_valid_iid(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_restricted_observe_valid_iid(data):
    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress("data", i),
            IID(Normal(0, 1), 21),
        )
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_restricted_sample_incorrect_iid_arguments(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_sample_incorrect_iid_arguments():
    for i in range(0, 100):
        _ = sample(
            IndexedAddress("i", i),
            IID(Normal(0, 1)),
        )
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictSampleCallStructureRule.message
            )

        @staticmethod
        def test_restricted_sample_valid_iid(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_restricted_sample_valid_iid(data):
    for i in range(0, 100):
        _ = sample(
            IndexedAddress("i", i),
            IID(Normal(0, 1), 12),
        )
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_restricted_observe_incorrect_iid_missing_argument(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_observe_incorrect_iid_missing_argument(data):
    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress(data, i),
            IID(Normal(0, 1)),
        )
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictObserveCallStructureRule.message
            )

        @staticmethod
        def test_restricted_indexed_address(default_linter: Linter) -> None:
            code = """
@probabilistic_program
def test_restricted_indexed_address(data):
    return sample(
        IndexedAddress(":)", 21),
        Normal(0, 1),
    )
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_restricted_indexed_address_nested(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_indexed_address_nested(data):
    return sample(
        IndexedAddress(
            IndexedAddress(
                IndexedAddress(
                    "nesting!",
                    12,
                ),
                1290478,
            ),
            21,
        ),
        Normal(0, 1),
    )
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_restricted_indexed_address_missing_address(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_indexed_address_missing_address(
    data,
):
    return sample(IndexedAddress(21), Normal(0, 1))
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictIndexedAddressCallStructureRule.message
            )

        @staticmethod
        def test_restricted_indexed_address_missing_number(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_indexed_address_missing_number(data):
    return sample(IndexedAddress("i"), Normal(0, 1))
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictIndexedAddressCallStructureRule.message
            )

    class TestVectorConstructor:
        @staticmethod
        def test_restricted_vector_constructor_size(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_vector_constructor_size(data):
    return Vector(12)
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_restricted_vector_constructor_size_fill(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_vector_constructor_size_fill(data):
    return Vector(12, fill=-1)
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_restricted_vector_constructor_size_fill_type(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_vector_constructor_size_fill_type(data):
    return Vector(12, fill=-1, t=int)
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_restricted_vector_constructor_missing_argument(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_vector_constructor_missing_argument(data):
    return Vector()
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictVectorConstructorCallStructureRule.message
            )

        @staticmethod
        def test_restricted_vector_constructor_additional_argument(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_vector_constructor_additional_argument(data):
    return Vector(12, -1, fill=-1, t=int)
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictVectorConstructorCallStructureRule.message
            )

    class TestArrayConstructor:
        @staticmethod
        def test_restricted_array_constructor_size(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_array_constructor_size(data):
    return Array((256, 256, 3))
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_restricted_array_constructor_size_fill(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_array_constructor_size_fill(data):
    return Array((256, 256, 3), fill=-1)
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_restricted_array_constructor_size_fill_type(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_array_constructor_size_fill_type(data):
    return Array((256, 256, 3), fill=-1, t=int)
            """
            diagnostics = default_linter.lint_code(code)
            assert not diagnostics

        @staticmethod
        def test_restricted_array_constructor_missing_argument(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_array_constructor_missing_argument(data):
    return Array()
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictArrayConstructorCallStructureRule.message
            )

        @staticmethod
        def test_restricted_array_constructor_additional_argument(
            default_linter: Linter,
        ) -> None:
            code = """
@probabilistic_program
def test_restricted_array_constructor_additional_argument(data):
    return Array((256, 256, 3), -1, fill=-1, t=int)
            """
            diagnostics = default_linter.lint_code(code)
            assert len(diagnostics) == 1
            assert diagnostics[0].severity == Severity.ERROR
            assert (
                diagnostics[0].message
                == rules.RestrictArrayConstructorCallStructureRule.message
            )


class TestUnrecommendedUseCases:
    @staticmethod
    def test_unrecommended_use_case_class(default_linter: Linter) -> None:
        code = """
@probabilistic_program
class TestUnrecommendedUseCaseClass:
    pass
    """
        diagnostics = default_linter.lint_code(code)
        assert len(diagnostics) == 1
        assert diagnostics[0].severity == Severity.INFORMATION

    @staticmethod
    def test_unrecommended_use_case_async_function(
        default_linter: Linter,
    ) -> None:
        code = """
@probabilistic_program
async def test_unrecommended_use_case_async_function():
    return "some promise"
    """
        diagnostics = default_linter.lint_code(code)
        assert len(diagnostics) == 1
        assert diagnostics[0].severity == Severity.INFORMATION

    @staticmethod
    def test_unchecked_if_main(default_linter: Linter) -> None:
        code = """
message = "This file is not intended for execution"

if __name__ == f"__{'main'}__":
    raise RuntimeError(f"{message}!")

raise RuntimeError(message.rsplit(" ", 1)[0] + " usage!")
    """
        diagnostics = default_linter.lint_code(code)
        assert not diagnostics
