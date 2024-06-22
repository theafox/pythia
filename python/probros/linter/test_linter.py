"""This contains tests for the probabilistic programming linter using `pytest`.

The tests validate the functionality of the linter to ensure proper
functionality, i.e. it correctly identifies and flags invalid code patterns in
probabilistic programs. Each test case checks specific rules. They all parse
the code as a string and match the resulting diagnostics against whats
expected.

This test-file and the test-cases are intended to be used with `pytest`. Its
fixture feature is used to parse a default probabilistic program to each
test-case.

The names of the test-cases follow the following pattern:
```
    test_(prohibited|restrict(ed)?)_<the rule name>_<any sub-test-cases>
```

Fixtures:
    - default_linter: A `pytest` fixture that provides a default instance of
        the probabilistic program linter.
"""

# type: ignore
import pytest
import rules
from diagnostic import Severity

from linter import Linter, default_probabilistic_program_linter


@pytest.fixture
def default_linter() -> Linter:
    return default_probabilistic_program_linter()


def test_valid_probabilistic_program(default_linter: Linter):
    code = """
@probros.probabilistic_program
def valid_probabilistic_program(data):
    probability = probros.sample("p", probros.Uniform(0, 1))
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("flip", i),
            probros.Bernoulli(probability),
        )
    return probability
"""
    diagnostics = default_linter.lint_code(code)
    assert not diagnostics


def test_unrecognized_decorator_addition(default_linter: Linter):
    code = """
@1 + 1
def unverifiable_function_add_decorator():
    pass
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.WARNING


def test_unrecognized_decorator_string(default_linter: Linter):
    code = """
@"hello decorator!"
def unverifiable_function_string_decorator():
    pass
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.WARNING


def test_unrecognized_decorator_matching_string(default_linter: Linter):
    code = """
@"probabilistic_program"
def unverifiable_function_string_decorator_probabilistic_program():
    pass
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.WARNING


def test_prohibited_fstring(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_fstring(data):
    probability = probros.sample("p", probros.Uniform(0, 1))
    for i in range(0, len(data)):
        address = f"flip[{i}]"
        probros.observe(data[i], address, probros.Bernoulli(probability))
    return probability
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 2
    assert all(
        diagnostic.severity == Severity.ERROR for diagnostic in diagnostics
    )
    messages = list(map(lambda diagnostic: diagnostic.message, diagnostics))
    assert rules.NoFstringRule.message in messages
    assert rules.RestrictObserveCallStructureRule.message in messages


def test_prohibited_deconstructor(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_deconstructor(data):
    mean, stddev = 2, 0.3
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Normal(mean, stddev),
        )
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.NoDeconstructorRule.message


def test_prohibited_nested_function(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_nested(data):
    @probros.probabilistic_program
    def invalidly_nested_probabilistic_program():
        probability = probros.sample("p", probros.Uniform(0, 1))
        for i in range(0, len(data)):
            probros.observe(
                data[i],
                f"flip[{i}]",
                probros.Bernoulli(probability),
            )
        return probability

    return invalidly_nested_probabilistic_program()
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.NoNestedFunctionsRule.message


def test_unchecked_code_decorator_definition(default_linter: Linter):
    code = """
def unchecked_duplicate_decorator(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        func(*args, **kwargs)

    return wrapper
"""
    diagnostics = default_linter.lint_code(code)
    assert not diagnostics


def test_unchecked_code_different_decorator_usage(default_linter: Linter):
    code = """
@unchecked_duplicate_decorator
def unchecked_function():
    VAR = f"This should {'allow'} anything!"

    def unchecked_nested_function(arg: str) -> str:
        return f"{arg=} including f-strings"

    VAR += "\\nand nested functions"
    return unchecked_nested_function(VAR)
"""
    diagnostics = default_linter.lint_code(code)
    assert not diagnostics


def test_valid_probabilistic_class_method(default_linter: Linter):
    code = """
class ClassContainingProbabilisticProgram:
    @probros.probabilistic_program
    def valid_probabilistic_program_in_class(self):
        count: int = 0
        for i in range(0, self.length):
            probability = probros.sample(
                probros.IndexedAddress("this", i),
                probros.Uniform(0, 1),
            )
            if probability < 0.1:
                return
            else:
                count += 1
"""
    diagnostics = default_linter.lint_code(code)
    assert not diagnostics


def test_prohibited_fstring_in_class_method(default_linter: Linter):
    code = """
class ClassContainingProbabilisticProgram:
    @probros.probabilistic_program
    def invalid_probabilistic_program_in_class_fstring(self):
        count: int = 0
        for i in range(0, self.length):
            address = f"this[{i}]"
            probability = probros.sample(address, probros.Uniform(0, 1))
            if probability < 0.1:
                return
            else:
                count += 1
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 2
    assert all(
        diagnostic.severity == Severity.ERROR for diagnostic in diagnostics
    )
    messages = list(map(lambda diagnostic: diagnostic.message, diagnostics))
    assert rules.NoFstringRule.message in messages
    assert rules.RestrictSampleCallStructureRule.message in messages


def test_prohibited_nested_class(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_nested_class():
    class InvalidlyNestedClass:
        pi = 3

    return InvalidNestedClass.pi
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.NoNestedClassesRule.message


def test_valid_probabilistic_program_in_function(default_linter: Linter):
    code = """
def outer_function():
    @probros.probabilistic_program
    def valid_probabilistic_program_in_function(data: list[int]):
        for i in range(0, len(data)):
            probros.observe(
                data[i],
                probros.IndexedAddress("data", i),
                probros.Poisson(0.7),
            )
"""
    diagnostics = default_linter.lint_code(code)
    assert not diagnostics


def test_prohibited_fstring_in_function(default_linter: Linter):
    code = """
def outer_function():
    @probros.probabilistic_program
    def invalid_probabilistic_program_in_function_fstring(data: list[float]):
        for i in range(0, len(data)):
            address = f"data[{i}]"
            probros.observe(
                data[i],
                address,
                probros.Poisson(0.2),
            )
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 2
    assert all(
        diagnostic.severity == Severity.ERROR for diagnostic in diagnostics
    )
    messages = list(map(lambda diagnostic: diagnostic.message, diagnostics))
    assert rules.NoFstringRule.message in messages
    assert rules.RestrictObserveCallStructureRule.message in messages


def test_prohibited_delete(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_delete(data):
    sum = 0
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Uniform(0, 1),
        )
        sum += data[i]
    del sum
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.NoDeleteStatementRule.message


def test_prohibited_type_aliasing(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_type_aliasing():
    type Probabilities = list[probros.Beta]
    probability: Probabilities = []
    for i in range(0, 5):
        probability += probros.Beta(0.1, 0.5)
    return probability
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.NoTypeAliasRule.message


def test_prohibited_asynchronous_for(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_asynchronous_for(data):
    probability = probros.Gamma(0.2, 0.9)
    if probability < 0.5:
        return False
    else:
        async for i in range(0, len(data)):
            probros.observe(
                data[i],
                probros.IndexedAddress("data", i),
                probros.Gamma(0.2, 0.9),
            )
        return True
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.NoAsynchronousStatementRule.message


def test_prohibited_with_file(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_with_file(filepath):
    with open(filepath) as file:
        data = file.readall()
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Uniform(0, 1),
        )
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.NoWithStatementRule.message


def test_prohibited_with_variables(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_with_variables(generator):
    with generator() as data:
        for i in range(0, len(data)):
            probros.observe(
                data[i],
                probros.IndexedAddress("data", i),
                probros.Uniform(0, 1),
            )
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.NoWithStatementRule.message


def test_restricted_for_iterable(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_for_iterable(data):
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
    assert diagnostics[0].message == rules.RestrictForLoopRule.message


def test_restricted_for_constant(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_for_constant(data):
    step = 0
    for _ in "this shouldn't work either!":
        probros.observe(data[step], "hi!", probros.Uniform(0, 1))
        step += 1
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.RestrictForLoopRule.message


def test_prohibited_walrus(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_walrus_operator(data):
    if (length := len(data)) > 10:
        for i in range(0, length):
            probros.observe(
                data[i],
                probros.IndexedAddress("data", i),
                probros.Uniform(0, 1),
            )
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.NoWalrusOperatorRule.message


def test_restricted_binary_operators_shift(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_shift_operator(n):
    return 1 << n
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.RestrictBinaryOperatorsRule.message


def test_restricted_binary_operators_bitwise(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_bitwise_operator(a, b, c, d):
    result = a & b
    result = result | c
    result = result ^ d
    return result
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 3
    assert all(
        diagnostic.severity == Severity.ERROR for diagnostic in diagnostics
    )
    assert all(
        diagnostic.message == rules.RestrictBinaryOperatorsRule.message
        for diagnostic in diagnostics
    )


def test_restricted_unary_operator_bitwise(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_bitwise_complement(n):
    return ~n
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.RestrictUnaryOperatorsRule.message


def test_prohibited_lambda(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_lambda(data):
    data = filter(lambda point: point >= 0, data)
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Gamma(0.1, 0.5),
        )
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.NoLambdaRule.message


def test_prohibited_inline_if(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_inline_if(probability):
    probability = 0 if probability < 0 else probability
    i = 0
    while True:
        sample = probros.sample(
            probros.IndexedAddress("data", i),
            probros.Bernoulli(probability),
        )
        if sample == 1:
            break
        i += 1
    return i
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.NoInlineIfRule.message


def test_prohibited_dictionary(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_dictionary(data):
    details = {
        "data": (data := data),
        "length": (length := data),
        "sum": (zum := data),
        "mean": zum / length,
    }

    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Uniform(0, 1),
        )

    details["remark"] = "hello world!"
    return details
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.NoDictionaryRule.message


def test_prohibited_set(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_set(data):
    reduced = set()
    for i in range(0, len(data)):
        reduced.add(data[i])
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Uniform(0, 1),
        )
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 2
    assert all(
        diagnostic.severity == Severity.ERROR for diagnostic in diagnostics
    )
    messages = list(map(lambda diagnostic: diagnostic.message, diagnostics))
    assert rules.NoSetRule.message in messages
    assert rules.NoStandaloneExpressionRule.message in messages


def test_prohibited_comprehension_list(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_list_comprehension():
    return [2**n for n in range(10)]
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert (
        diagnostics[0].message == rules.NoComprehensionAndGeneratorRule.message
    )


def test_prohibited_comprehension_set(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_set_comprehension():
    return {2**n for n in range(10)}
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert (
        diagnostics[0].message == rules.NoComprehensionAndGeneratorRule.message
    )


def test_prohibited_comprehension_dictionary(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_dictionary_comprehension():
    return {n: 2**n for n in range(10)}
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert (
        diagnostics[0].message == rules.NoComprehensionAndGeneratorRule.message
    )


def test_prohibited_generator(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_generator():
    return sum(2**n for n in range(10))
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert (
        diagnostics[0].message == rules.NoComprehensionAndGeneratorRule.message
    )


def test_prohibited_asynchronous_await(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_asynchronous_await(data):
    probabilities = (
        await invalid_probabilistic_program_asynchronous_generator()
    )
    for i in range(0, len(probabilities)):
        if probabilities[i] > 0.9:
            return True
    return False
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.NoAsynchronousExpressionRule.message


def test_prohibited_asynchronous_generator(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_asynchronous_generator():
    return [probros.Normal(n, n * 0.1) async for n in range(10)]
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 2
    assert all(
        diagnostic.severity == Severity.ERROR for diagnostic in diagnostics
    )
    messages = list(map(lambda diagnostic: diagnostic.message, diagnostics))
    assert rules.NoAsynchronousExpressionRule.message in messages
    assert rules.NoComprehensionAndGeneratorRule.message in messages


def test_prohibited_yield(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_yield(data):
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Uniform(0, 1),
        )
        yield data[i]
"""
    default_linter.extensive_diagnosis = True
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 2
    assert all(
        diagnostic.severity == Severity.ERROR for diagnostic in diagnostics
    )
    messages = list(map(lambda diagnostic: diagnostic.message, diagnostics))
    assert rules.NoYieldRule.message in messages
    assert rules.NoStandaloneExpressionRule.message in messages


def test_prohibited_yield_from(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_yield_from(data):
    yield from invalid_probabilistic_program_yield(data)
"""
    default_linter.extensive_diagnosis = True
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 2
    assert all(
        diagnostic.severity == Severity.ERROR for diagnostic in diagnostics
    )
    messages = list(map(lambda diagnostic: diagnostic.message, diagnostics))
    assert rules.NoYieldRule.message in messages
    assert rules.NoStandaloneExpressionRule.message in messages


def test_prohibited_starred(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_starred(data):
    zum = sum(*data)
    for i in range(0, len(data)):
        data[i] /= zum
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Dirac(0.25),
        )
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.NoStarredRule.message


def test_prohibited_slice(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_slice(data):
    data = data[0:100]
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Dirac(0.25),
        )
    return probros.sample(
        probros.IndexedAddress("data", len(data)),
        probros.Dirac(0.25),
    )
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.NoSliceRule.message


def test_valid_probabilistic_program_array_assign(default_linter: Linter):
    code = """
@probros.probabilistic_program
def valid_probabilistic_program_array_assign(data):
    details = list()
    details[0] = data
    details[1] = sum(data)
    details[2] = len(data)
    details[3] = details[1] / details[2]
    return details
"""
    diagnostics = default_linter.lint_code(code)
    assert not diagnostics


def test_prohibited_attribute_assign(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_attribute_assign(data):
    data.sum = sum(data)
    return data.sum
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.NoAttributeAssignRule.message


def test_prohibited_standalone_expression_allowed_observe(
    default_linter: Linter,
):
    code = """
@probros.probabilistic_program
def valid_probabilistic_program_standalone_expression_observe_call():
    probros.observe(
        12,
        "standalone_observe_call",
        probros.Uniform(0, 1),
    )
"""
    diagnostics = default_linter.lint_code(code)
    assert not diagnostics


def test_prohibited_standalone_expression_allowed_factor(
    default_linter: Linter,
):
    code = """
@probros.probabilistic_program
def valid_probabilistic_program_standalone_expression_factor_call():
    probros.factor(0.0124)
"""
    diagnostics = default_linter.lint_code(code)
    assert not diagnostics


def test_prohibited_standalone_expression_function_call(
    default_linter: Linter,
):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_standalone_expression_function_call(n):
    initialize_context()
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.NoStandaloneExpressionRule.message


def test_prohibited_standalone_expression_calculations(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_standalone_expression_calculation(n):
    1 + 2**3 / 4 // 5
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.NoStandaloneExpressionRule.message


def test_prohibited_multiple_subscript(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_subscript(data):
    data[0, -1] = data[-1], data[0]
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Dirac(0.25),
        )
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert diagnostics[0].message == rules.NoMultipleSubscriptRule.message


def test_restricted_observe_call_address_number(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_observe_number_address(data):
    probability = probros.sample("p", probros.Uniform(0, 1))
    for i in range(0, len(data)):
        probros.observe(data[i], 123, probros.Bernoulli(probability))
    return probability
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert (
        diagnostics[0].message
        == rules.RestrictObserveCallStructureRule.message
    )


def test_restricted_observe_call_address_variable(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_observe_variable_address(data: list[float]):
    for i in range(0, len(data)):
        address = probros.IndexedAddress("data", i)
        probros.observe(
            data[i],
            address,
            probros.Poisson(0.2),
        )
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert (
        diagnostics[0].message
        == rules.RestrictObserveCallStructureRule.message
    )


def test_restrict_observe_structure_two_keyword_arguments(
    default_linter: Linter,
):
    code = """
@probros.probabilistic_program
def valid_probabilistic_program_observe_keyword_arguments(data: list[float]):
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            distribution=probros.Poisson(0.2),
            address=probros.IndexedAddress("data", i),
        )
"""
    diagnostics = default_linter.lint_code(code)
    assert not diagnostics


def test_restrict_observe_structure_one_keyword_argument(
    default_linter: Linter,
):
    code = """
@probros.probabilistic_program
def valid_probabilistic_program_observe_keyword_argument(data: list[float]):
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            distribution=probros.Poisson(0.2),
        )
"""
    diagnostics = default_linter.lint_code(code)
    assert not diagnostics


def test_restrict_observe_structure_incorrect_ordering(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_observe_keyword_arguments_ordering(
    data: list[float],
):
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            address=probros.IndexedAddress("data", i),
        )
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert (
        diagnostics[0].message
        == rules.RestrictObserveCallStructureRule.message
    )


def test_restrict_observe_structure_missing_positional(
    default_linter: Linter,
):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_observe_missing_positional(
    data: list[float],
):
    for i in range(0, len(data)):
        probros.observe(
            value=data[i],
            distribution=probros.Poisson(0.2),
            address=probros.IndexedAddress("data", i),
        )
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert (
        diagnostics[0].message
        == rules.RestrictObserveCallStructureRule.message
    )


def test_restricted_sample_structure(default_linter: Linter):
    code = """
@probros.probabilistic_program
def valid_probabilistic_program_sample(data: list[float]):
    return sample("p", probros.Dirac(True))
"""
    diagnostics = default_linter.lint_code(code)
    assert not diagnostics


def test_restricted_sample_structure_incorrect_address_number(
    default_linter: Linter,
):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_sample_incorrect_address_number(
    data: list[float],
):
    return probros.sample(123, probros.Dirac(True))
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert (
        diagnostics[0].message == rules.RestrictSampleCallStructureRule.message
    )


def test_restricted_sample_structure_missing_argument(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_sample_missing_argument(
    data: list[float],
):
    return probros.sample("p")
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert (
        diagnostics[0].message == rules.RestrictSampleCallStructureRule.message
    )


def test_restricted_sample_structure_incorrect_keyword_argument(
    default_linter: Linter,
):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_sample_keyword_argument(
    data: list[float],
):
    return probros.sample("p", distribution=probros.Uniform(0, 1))
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert (
        diagnostics[0].message == rules.RestrictSampleCallStructureRule.message
    )


def test_restricted_factor_valid_keyword(default_linter: Linter):
    code = """
@probros.probabilistic_program
def valid_probabilistic_program_factor_string_address():
    probros.factor(0.001, address="data")
"""
    diagnostics = default_linter.lint_code(code)
    assert not diagnostics


def test_restricted_factor_valid_indexed_address(default_linter: Linter):
    code = """
@probros.probabilistic_program
def valid_probabilistic_program_factor_indexed_address():
    probros.factor(0.001, probros.IndexedAddress("data", 0))
"""
    diagnostics = default_linter.lint_code(code)
    assert not diagnostics


def test_restricted_observe_missing_expression(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_factor_missing_expression():
    probros.factor()
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert (
        diagnostics[0].message == rules.RestrictFactorCallStructureRule.message
    )


def test_restricted_observe_additional_argument(default_linter: Linter):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_factor_additional_arguments():
    probros.factor(0.123, "address", probros.Beta(0.1, 0.2))
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert (
        diagnostics[0].message == rules.RestrictFactorCallStructureRule.message
    )


def test_restricted_observe_valide_broadcasted(default_linter: Linter):
    code = """
@probros.probabilistic_program
def valid_probabilistic_program_broadcast_statement(data):
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Broadcasted(probros.Normal(0, 1)),
        )
"""
    diagnostics = default_linter.lint_code(code)
    assert not diagnostics


def test_restricted_sample_incorrect_broadcasted_arguments(
    default_linter: Linter,
):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_broadcast_statement_constant():
    for i in range(0, 100):
        _ = probros.sample(
            probros.IndexedAddress("i", i),
            probros.Broadcasted(probros.Normal(0, 1), 12),
        )
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert (
        diagnostics[0].message == rules.RestrictSampleCallStructureRule.message
    )


def test_restricted_sample_valid_iid(default_linter: Linter):
    code = """
@probros.probabilistic_program
def valid_probabilistic_program_iid_statement(data):
    for i in range(0, 100):
        _ = probros.sample(
            probros.IndexedAddress("i", i),
            probros.IID(probros.Normal(0, 1), 12),
        )
"""
    diagnostics = default_linter.lint_code(code)
    assert not diagnostics


def test_restricted_observe_incorrect_iid_missing_argument(
    default_linter: Linter,
):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_iid_statement_missing_constant(data):
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress(data, i),
            probros.IID(probros.Normal(0, 1)),
        )
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert (
        diagnostics[0].message
        == rules.RestrictObserveCallStructureRule.message
    )


def test_restricted_indexed_address(
    default_linter: Linter,
):
    code = """
@probros.probabilistic_program
def valid_probabilistic_program_indexed_address(data):
    return probros.sample(
        probros.IndexedAddress(":)", 21),
        probros.Normal(0, 1),
    )
"""
    diagnostics = default_linter.lint_code(code)
    assert not diagnostics


def test_restricted_indexed_address_nested(
    default_linter: Linter,
):
    code = """
@probros.probabilistic_program
def valid_probabilistic_program_nested_indexed_address(data):
    return probros.sample(
        probros.IndexedAddress(
            probros.IndexedAddress(
                probros.IndexedAddress(
                    "nesting!",
                    12,
                ),
                1290478,
            ),
            21,
        ),
        probros.Normal(0, 1),
    )
"""
    diagnostics = default_linter.lint_code(code)
    assert not diagnostics


def test_restricted_indexed_address_missing_address(
    default_linter: Linter,
):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_invalid_indexed_address_call_no_address(
    data,
):
    return probros.sample(probros.IndexedAddress(21), probros.Normal(0, 1))
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert (
        diagnostics[0].message
        == rules.RestrictIndexedAddressCallStructureRule.message
    )


def test_restricted_indexed_address_missing_number(
    default_linter: Linter,
):
    code = """
@probros.probabilistic_program
def invalid_probabilistic_program_invalid_indexed_address_call_no_number(data):
    return probros.sample(probros.IndexedAddress("i"), probros.Normal(0, 1))
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.ERROR
    assert (
        diagnostics[0].message
        == rules.RestrictIndexedAddressCallStructureRule.message
    )


def test_unrecommended_use_case_class(default_linter: Linter):
    code = """
@probros.probabilistic_program
class UnrecommendedProbabilisticProgramDecoratorOnClass:
    pass
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.INFORMATION


def test_unrecommended_use_case_async_function(default_linter: Linter):
    code = """
@probros.probabilistic_program
async def unrecommended_probabilistic_program_decorator_on_async_function():
    return "some promise"
"""
    diagnostics = default_linter.lint_code(code)
    assert len(diagnostics) == 1
    assert diagnostics[0].severity == Severity.INFORMATION


def test_unchecked_if_main(default_linter: Linter):
    code = """
message = "This file is not intended for execution"

if __name__ == f"__{'main'}__":
    raise RuntimeError(f"{message}!")

raise RuntimeError(message.rsplit(" ", 1)[0] + " usage!")
"""
    diagnostics = default_linter.lint_code(code)
    assert not diagnostics
