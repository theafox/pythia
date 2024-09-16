# type: ignore
"""A simple demonstration of the linter.

This showcases the linter using the test-cases as examples. This demonstration
works best with the linter integrated into a development environment.

Author: T. Kaufmann <e12002221@student.tuwien.ac.at>
"""

from probros import *


@1 + 1
def test_unrecognized_decorator_addition():
    pass


@"hello decorator!"
def test_unrecognized_decorator_string():
    pass


@"probabilistic_program"
def test_unrecognized_decorator_matching_string():
    pass


@probabilistic_program
def test_valid_entry_point_positional_only_arguments(a, b, /, c):
    return a + b + c


@probabilistic_program
def test_invalid_entry_point_keyword_argument(data=None):
    return data


@probabilistic_program
def test_invalid_entry_point_keyword_only_argument(a, *args, b):
    return a * b


@probabilistic_program
def test_invalid_entry_point_catch_argument(data, *args):
    return data


@probabilistic_program
def test_invalid_entry_point_catch_keyword_argument(data, **kwargs):
    return data


@probabilistic_program
def test_warned_entry_point_typing(data: list[int]):
    return data


@probabilistic_program
def test_invalid_entry_point_typed_keyword_argument(data: list[int] = []):
    return data


def test_unchecked_code_decorator_definition(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        func(*args, **kwargs)

    return wrapper


@test_unchecked_code_decorator_definition
def test_unchecked_code_different_decorator_usage():
    VAR = f"This should {'allow'} anything!"

    def test_unchecked_code_different_decorator_usage_nested_function(arg):
        return f"{arg=} including f-strings"

    VAR += "\\nand nested functions"
    return test_unchecked_code_different_decorator_usage_nested_function(VAR)


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


@probabilistic_program
def test_invalid_probabilistic_program(data):
    probability = sample("p", Uniform(0, 1))
    for i in range(0, len(data)):
        address = f"flip[{i}]"
        observe(data[i], address, Bernoulli(probability))
    return probability


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


def test_valid_probabilistic_program_in_function_outer():
    @probabilistic_program
    def test_valid_probabilistic_program_in_function(data):
        for i in range(0, len(data)):
            observe(
                data[i],
                IndexedAddress("data", i),
                Poisson(0.7),
            )


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


@probabilistic_program
def test_prohibited_nested_class():
    class TestProhibitedNestedClassNested:
        pi = 3

    return TestProhibitedNestedClassNested.pi


@probabilistic_program
def test_prohibited_import(degrees):
    import math

    return math.radians(degrees)


@probabilistic_program
def test_prohibited_import_from():
    from random import randint

    return randint(0, 10)


@probabilistic_program
def test_prohibited_gloabl():
    global x
    x = 23


@probabilistic_program
def test_prohibited_nonlocal():
    nonlocal x
    x = 23


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


@probabilistic_program
def test_prohibited_type_aliasing():
    type Probabilities = list[Beta]
    probability: Probabilities = []
    for i in range(0, 5):
        probability = probability + Beta(0.1, 0.5)
    return probability


@probabilistic_program
def test_allowed_array_assign(data):
    details = list()
    details[0] = data
    details[1] = sum(data)
    details[2] = len(data)
    details[3] = details[1] / details[2]
    return details


@probabilistic_program
def test_prohibited_deconstructor(data):
    mean, stddev = 2, 0.3
    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress("data", i),
            Normal(mean, stddev),
        )


@probabilistic_program
def test_prohibited_augmented_assign_addition(probability):
    probability += 0.01


@probabilistic_program
def test_prohibited_augmented_assign_and_bitwise(probability):
    probability ^= 0b1010


@probabilistic_program
def test_prohibited_augmented_assign_division(probability):
    probability /= 2


@probabilistic_program
def test_prohibited_augmented_assign_power(probability):
    probability **= 2


@probabilistic_program
def test_warned_annotated_assign_int(a):
    b: int = a


@probabilistic_program
def test_prohibited_chained_assign(data):
    x = y = data


@probabilistic_program
def test_prohibited_attribute_assign(data):
    data.sum = sum(data)
    return data.sum


@probabilistic_program
def test_prohibited_standalone_expression_allowed_observe():
    observe(
        12,
        "standalone_observe_call",
        Uniform(0, 1),
    )


@probabilistic_program
def test_prohibited_standalone_expression_allowed_factor():
    factor(0.0124)


@probabilistic_program
def test_prohibited_standalone_expression_function_call(n):
    initialize_context()


@probabilistic_program
def test_prohibited_standalone_expression_calculations(n):
    1 + 2**3 / 4 // 5


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


@probabilistic_program
def test_restricted_for_iterable_constant(data):
    step = 0
    for _ in "this shouldn't work either!":
        observe(data[step], "hi!", Uniform(0, 1))
        step += 1


@probabilistic_program
def test_prohibited_for_else(data):
    for i in range(0, 10):
        continue
    else:
        myvar = "hello"


@probabilistic_program
def test_prohibited_while_else(data):
    while False:
        continue
    else:
        myvar = "hello"


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


@probabilistic_program
def test_prohibited_with_variables(generator):
    with generator() as data:
        for i in range(0, len(data)):
            observe(
                data[i],
                IndexedAddress("data", i),
                Uniform(0, 1),
            )


@probabilistic_program
def test_prohibited_match(data):
    match data:
        case []:
            return False
        case _:
            return True


@probabilistic_program
def test_prohibited_asynchronous_function_definition(data):
    async def test_prohibited_asynchronous_function_definition_nested():
        return None


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


@probabilistic_program
def test_prohibited_asynchronous_with(path):
    async with open(path, "r"):
        return None


@probabilistic_program
def test_prohibited_pass(data):
    pass


@probabilistic_program
def test_valid_return(data):
    return None


@probabilistic_program
def test_prohibited_empty_return(data):
    return


@probabilistic_program
def test_prohibited_raise(data):
    raise RuntimeError("forbidden!")


@probabilistic_program
def test_prohibited_try_except(data):
    try:
        return None
    except:
        return None


@probabilistic_program
def test_prohibited_assert(data):
    assert True


@probabilistic_program
def test_restricted_unary_operator_bitwise(n):
    return ~n


@probabilistic_program
def test_restricted_binary_operators_shift(n):
    return 1 << n


@probabilistic_program
def test_restricted_binary_operators_bitwise(a, b, c, d):
    result = a & b
    result = result | c
    result = result ^ d
    return result


@probabilistic_program
def test_restricted_comparison_operators(a, b, c, d, e, f, g):
    result = a == b
    result = result != c
    result = result < d
    result = result <= e
    result = result > f
    result = result >= g
    return result


@probabilistic_program
def test_restricted_comparison_operators_is(a, b):
    return a is b


@probabilistic_program
def test_restricted_comparison_operators_is_not(a, b):
    return a is not b


@probabilistic_program
def test_restricted_comparison_operators_in(a, b):
    return a in b


@probabilistic_program
def test_restricted_comparison_operators_not_in(a, b):
    return a not in b


@probabilistic_program
def test_restricted_comparison_operators_multiple(a, b, c):
    return a < b <= c


@probabilistic_program
def test_prohibited_walrus(data):
    if (length := len(data)) > 10:
        for i in range(0, length):
            observe(
                data[i],
                IndexedAddress("data", i),
                Uniform(0, 1),
            )


@probabilistic_program
def test_prohibited_lambda(data):
    data = filter(lambda point: point >= 0, data)
    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress("data", i),
            Gamma(0.1, 0.5),
        )


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


@probabilistic_program
def test_prohibited_comprehension_list():
    return [2**n for n in range(10)]


@probabilistic_program
def test_prohibited_comprehension_set():
    return {2**n for n in range(10)}


@probabilistic_program
def test_prohibited_comprehension_dictionary():
    return {n: 2**n for n in range(10)}


@probabilistic_program
def test_prohibited_generator():
    return sum(2**n for n in range(10))


@probabilistic_program
def test_prohibited_asynchronous_await(data):
    probabilities = await test_prohibited_asynchronous_generator()
    for i in range(0, len(probabilities)):
        if probabilities[i] > 0.9:
            return True
    return False


@probabilistic_program
def test_prohibited_asynchronous_generator():
    return [Normal(n, n * 0.1) async for n in range(10)]


@probabilistic_program
def test_prohibited_yield(data):
    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress("data", i),
            Uniform(0, 1),
        )
        yield data[i]


@probabilistic_program
def test_prohibited_yield_from(data):
    yield from test_prohibited_yield(data)


@probabilistic_program
def test_prohibited_fstring():
    return f"prohibited {'f-string'}!"


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


@probabilistic_program
def test_prohibited_type_parameters_alias(data):
    type Alias[*Ts] = tuple[*Ts]


@probabilistic_program
def test_prohibited_type_parameters_function(data):
    def first[T](l: list[T]) -> T:
        return l[0]


@probabilistic_program
def test_prohibited_slice(data):
    data = data[0:100]
    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress("data", i),
            Dirac(0.25),
        )
    return sample(
        IndexedAddress("data", len(data)),
        Dirac(0.25),
    )


@probabilistic_program
def test_prohibited_multiple_subscript(data):
    data[0, -1] = data[-1], data[0]
    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress("data", i),
            Dirac(0.25),
        )


@probabilistic_program
def test_restricted_sample_structure(data):
    return sample("p", Dirac(True))


@probabilistic_program
def test_restricted_sample_structure_incorrect_address_number(data):
    return sample(123, Dirac(True))


@probabilistic_program
def test_restricted_sample_structure_missing_argument(data):
    return sample("p")


@probabilistic_program
def test_restricted_sample_structure_incorrect_keyword_argument(data):
    return sample("p", distribution=Uniform(0, 1))


@probabilistic_program
def test_restricted_observe_call_address_number(data):
    probability = sample("p", Uniform(0, 1))
    for i in range(0, len(data)):
        observe(data[i], 123, Bernoulli(probability))
    return probability


@probabilistic_program
def test_restricted_observe_call_address_variable(data):
    for i in range(0, len(data)):
        address = IndexedAddress("data", i)
        observe(
            data[i],
            address,
            Poisson(0.2),
        )


@probabilistic_program
def test_restrict_observe_structure_two_keyword_arguments(data):
    for i in range(0, len(data)):
        observe(
            data[i],
            distribution=Poisson(0.2),
            address=IndexedAddress("data", i),
        )


@probabilistic_program
def test_restrict_observe_structure_one_keyword_argument(data):
    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress("data", i),
            distribution=Poisson(0.2),
        )


@probabilistic_program
def test_restrict_observe_structure_incorrect_ordering(data):
    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress("data", i),
            address=IndexedAddress("data", i),
        )


@probabilistic_program
def test_restrict_observe_structure_missing_positional(data):
    for i in range(0, len(data)):
        observe(
            value=data[i],
            distribution=Poisson(0.2),
            address=IndexedAddress("data", i),
        )


@probabilistic_program
def test_restricted_factor_valid_keyword():
    factor(0.001, address="data")


@probabilistic_program
def test_restricted_factor_valid_indexed_address():
    factor(0.001, IndexedAddress("data", 0))


@probabilistic_program
def test_restricted_factor_missing_expression():
    factor()


@probabilistic_program
def test_restricted_factor_additional_argument():
    factor(0.123, "address", Beta(0.1, 0.2))


@probabilistic_program
def test_restricted_observe_valid_iid(data):
    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress("data", i),
            IID(Normal(0, 1), 21),
        )


@probabilistic_program
def test_restricted_sample_incorrect_iid_arguments():
    for i in range(0, 100):
        _ = sample(
            IndexedAddress("i", i),
            IID(Normal(0, 1)),
        )


@probabilistic_program
def test_restricted_sample_valid_iid(data):
    for i in range(0, 100):
        _ = sample(
            IndexedAddress("i", i),
            IID(Normal(0, 1), 12),
        )


@probabilistic_program
def test_restricted_observe_incorrect_iid_missing_argument(data):
    for i in range(0, len(data)):
        observe(
            data[i],
            IndexedAddress(data, i),
            IID(Normal(0, 1)),
        )


@probabilistic_program
def test_restricted_indexed_address(data):
    return sample(
        IndexedAddress(":)", 21),
        Normal(0, 1),
    )


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


@probabilistic_program
def test_restricted_indexed_address_missing_address(
    data,
):
    return sample(IndexedAddress(21), Normal(0, 1))


@probabilistic_program
def test_restricted_indexed_address_missing_number(data):
    return sample(IndexedAddress("i"), Normal(0, 1))


@probabilistic_program
def test_restricted_vector_constructor_size(data):
    return Vector(12)


@probabilistic_program
def test_restricted_vector_constructor_size_fill(data):
    return Vector(12, fill=-1)


@probabilistic_program
def test_restricted_vector_constructor_size_fill_type(data):
    return Vector(12, fill=-1, t=int)


@probabilistic_program
def test_restricted_vector_constructor_missing_argument(data):
    return Vector()


@probabilistic_program
def test_restricted_vector_constructor_additional_argument(data):
    return Vector(12, -1, fill=-1, t=int)


@probabilistic_program
def test_restricted_array_constructor_size(data):
    return Array((256, 256, 3))


@probabilistic_program
def test_restricted_array_constructor_size_fill(data):
    return Array((256, 256, 3), fill=-1)


@probabilistic_program
def test_restricted_array_constructor_size_fill_type(data):
    return Array((256, 256, 3), fill=-1, t=int)


@probabilistic_program
def test_restricted_array_constructor_missing_argument(data):
    return Array()


@probabilistic_program
def test_restricted_array_constructor_additional_argument(data):
    return Array((256, 256, 3), -1, fill=-1, t=int)


@probabilistic_program
class TestUnrecommendedUseCaseClass:
    pass


@probabilistic_program
async def test_unrecommended_use_case_async_function():
    return "some promise"


message = "This file is not intended for execution"

if __name__ == f"__{'main'}__":
    raise RuntimeError(f"{message}!")

raise RuntimeError(message.rsplit(" ", 1)[0] + " usage!")
