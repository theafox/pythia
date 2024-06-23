# type: ignore
import probros


@probros.probabilistic_program
def test_valid_probabilistic_program(data):
    probability = probros.sample("p", probros.Uniform(0, 1))
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("flip", i),
            probros.Bernoulli(probability),
        )
    return probability


@1 + 1
def test_unrecognized_decorator_addition():
    pass


@"hello decorator!"
def test_unrecognized_decorator_string():
    pass


@"probabilistic_program"
def test_unrecognized_decorator_matching_string():
    pass


@probros.probabilistic_program
def test_prohibited_fstring(data):
    probability = probros.sample("p", probros.Uniform(0, 1))
    for i in range(0, len(data)):
        address = f"flip[{i}]"
        probros.observe(data[i], address, probros.Bernoulli(probability))
    return probability


@probros.probabilistic_program
def test_prohibited_deconstructor(data):
    mean, stddev = 2, 0.3
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Normal(mean, stddev),
        )


@probros.probabilistic_program
def test_prohibited_nested_function(data):
    @probros.probabilistic_program
    def test_prohibited_nested_function_nested():
        probability = probros.sample("p", probros.Uniform(0, 1))
        for i in range(0, len(data)):
            probros.observe(
                data[i],
                f"flip[{i}]",
                probros.Bernoulli(probability),
            )
        return probability

    return test_prohibited_nested_function_nested()


def test_unchecked_code_decorator_definition(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        func(*args, **kwargs)

    return wrapper


@unchecked_duplicate_decorator
def test_unchecked_code_different_decorator_usage():
    VAR = f"This should {'allow'} anything!"

    def test_unchecked_code_different_decorator_usage_nested_function(arg):
        return f"{arg=} including f-strings"

    VAR += "\\nand nested functions"
    return test_unchecked_code_different_decorator_usage_nested_function(VAR)


class TestValidProbabilisticClassMethodOuter:
    @probros.probabilistic_program
    def test_valid_probabilistic_class_method(self):
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


class TestProhibitedFstringInClassMethod:
    @probros.probabilistic_program
    def test_prohibited_fstring_in_class_method(self):
        count: int = 0
        for i in range(0, self.length):
            address = f"this[{i}]"
            probability = probros.sample(address, probros.Uniform(0, 1))
            if probability < 0.1:
                return
            else:
                count += 1


@probros.probabilistic_program
def test_prohibited_nested_class():
    class TestProhibitedNestedClassNested:
        pi = 3

    return TestProhibitedNestedClassNested.pi


def test_valid_probabilistic_program_in_function_outer():
    @probros.probabilistic_program
    def test_valid_probabilistic_program_in_function(data: list[int]):
        for i in range(0, len(data)):
            probros.observe(
                data[i],
                probros.IndexedAddress("data", i),
                probros.Poisson(0.7),
            )


def test_prohibited_fstring_in_function_outer():
    @probros.probabilistic_program
    def test_prohibited_fstring_in_function(data: list[float]):
        for i in range(0, len(data)):
            address = f"data[{i}]"
            probros.observe(
                data[i],
                address,
                probros.Poisson(0.2),
            )


@probros.probabilistic_program
def test_prohibited_delete(data):
    sum = 0
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Uniform(0, 1),
        )
        sum += data[i]
    del sum


@probros.probabilistic_program
def test_prohibited_type_aliasing():
    type Probabilities = list[probros.Beta]
    probability: Probabilities = []
    for i in range(0, 5):
        probability += probros.Beta(0.1, 0.5)
    return probability


@probros.probabilistic_program
def test_prohibited_asynchronous_for(data):
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


@probros.probabilistic_program
def test_prohibited_with_file(filepath):
    with open(filepath) as file:
        data = file.readall()
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Uniform(0, 1),
        )


@probros.probabilistic_program
def test_prohibited_with_variables(generator):
    with generator() as data:
        for i in range(0, len(data)):
            probros.observe(
                data[i],
                probros.IndexedAddress("data", i),
                probros.Uniform(0, 1),
            )


@probros.probabilistic_program
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


@probros.probabilistic_program
def test_restricted_for_constant(data):
    step = 0
    for _ in "this shouldn't work either!":
        probros.observe(data[step], "hi!", probros.Uniform(0, 1))
        step += 1


@probros.probabilistic_program
def test_prohibited_walrus(data):
    if (length := len(data)) > 10:
        for i in range(0, length):
            probros.observe(
                data[i],
                probros.IndexedAddress("data", i),
                probros.Uniform(0, 1),
            )


@probros.probabilistic_program
def test_restricted_binary_operators_shift(n):
    return 1 << n


@probros.probabilistic_program
def test_restricted_binary_operators_bitwise(a, b, c, d):
    result = a & b
    result = result | c
    result = result ^ d
    return result


@probros.probabilistic_program
def test_restricted_unary_operator_bitwise(n):
    return ~n


@probros.probabilistic_program
def test_prohibited_lambda(data):
    data = filter(lambda point: point >= 0, data)
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Gamma(0.1, 0.5),
        )


@probros.probabilistic_program
def test_prohibited_inline_if(probability):
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


@probros.probabilistic_program
def test_prohibited_dictionary(data):
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


@probros.probabilistic_program
def test_prohibited_set(data):
    reduced = set()
    for i in range(0, len(data)):
        reduced.add(data[i])
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Uniform(0, 1),
        )


@probros.probabilistic_program
def test_prohibited_comprehension_list():
    return [2**n for n in range(10)]


@probros.probabilistic_program
def test_prohibited_comprehension_set():
    return {2**n for n in range(10)}


@probros.probabilistic_program
def test_prohibited_comprehension_dictionary():
    return {n: 2**n for n in range(10)}


@probros.probabilistic_program
def test_prohibited_generator():
    return sum(2**n for n in range(10))


@probros.probabilistic_program
def test_prohibited_asynchronous_await(data):
    probabilities = await test_prohibited_asynchronous_generator()
    for i in range(0, len(probabilities)):
        if probabilities[i] > 0.9:
            return True
    return False


@probros.probabilistic_program
def test_prohibited_asynchronous_generator():
    return [probros.Normal(n, n * 0.1) async for n in range(10)]


@probros.probabilistic_program
def test_prohibited_yield(data):
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Uniform(0, 1),
        )
        yield data[i]


@probros.probabilistic_program
def test_prohibited_yield_from(data):
    yield from test_prohibited_yield(data)


@probros.probabilistic_program
def test_prohibited_starred(data):
    zum = sum(*data)
    for i in range(0, len(data)):
        data[i] /= zum
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Dirac(0.25),
        )


@probros.probabilistic_program
def test_prohibited_slice(data):
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


@probros.probabilistic_program
def test_valid_probabilistic_program_array_assign(data):
    details = list()
    details[0] = data
    details[1] = sum(data)
    details[2] = len(data)
    details[3] = details[1] / details[2]
    return details


@probros.probabilistic_program
def test_prohibited_attribute_assign(data):
    data.sum = sum(data)
    return data.sum


@probros.probabilistic_program
def test_prohibited_standalone_expression_allowed_observe():
    probros.observe(
        12,
        "standalone_observe_call",
        probros.Uniform(0, 1),
    )


@probros.probabilistic_program
def test_prohibited_standalone_expression_allowed_factor():
    probros.factor(0.0124)


@probros.probabilistic_program
def test_prohibited_standalone_expression_function_call(n):
    initialize_context()


@probros.probabilistic_program
def test_prohibited_standalone_expression_calculations(n):
    1 + 2**3 / 4 // 5


@probros.probabilistic_program
def test_prohibited_multiple_subscript(data):
    data[0, -1] = data[-1], data[0]
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Dirac(0.25),
        )


@probros.probabilistic_program
def test_restricted_observe_call_address_number(data):
    probability = probros.sample("p", probros.Uniform(0, 1))
    for i in range(0, len(data)):
        probros.observe(data[i], 123, probros.Bernoulli(probability))
    return probability


@probros.probabilistic_program
def test_restricted_observe_call_address_variable(data: list[float]):
    for i in range(0, len(data)):
        address = probros.IndexedAddress("data", i)
        probros.observe(
            data[i],
            address,
            probros.Poisson(0.2),
        )


@probros.probabilistic_program
def test_restrict_observe_structure_two_keyword_arguments(data: list[float]):
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            distribution=probros.Poisson(0.2),
            address=probros.IndexedAddress("data", i),
        )


@probros.probabilistic_program
def test_restrict_observe_structure_one_keyword_argument(data: list[float]):
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            distribution=probros.Poisson(0.2),
        )


@probros.probabilistic_program
def test_restrict_observe_structure_incorrect_ordering(
    data: list[float],
):
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            address=probros.IndexedAddress("data", i),
        )


@probros.probabilistic_program
def test_restrict_observe_structure_missing_positional(
    data: list[float],
):
    for i in range(0, len(data)):
        probros.observe(
            value=data[i],
            distribution=probros.Poisson(0.2),
            address=probros.IndexedAddress("data", i),
        )


@probros.probabilistic_program
def test_restricted_sample_structure(data: list[float]):
    return probros.sample("p", probros.Dirac(True))


@probros.probabilistic_program
def test_restricted_sample_structure_incorrect_address_number(
    data: list[float],
):
    return probros.sample(123, probros.Dirac(True))


@probros.probabilistic_program
def test_restricted_sample_structure_missing_argument(
    data: list[float],
):
    return probros.sample("p")


@probros.probabilistic_program
def test_restricted_sample_structure_incorrect_keyword_argument(
    data: list[float],
):
    return probros.sample("p", distribution=probros.Uniform(0, 1))


@probros.probabilistic_program
def test_restricted_factor_valid_keyword():
    probros.factor(0.001, address="data")


@probros.probabilistic_program
def test_restricted_factor_valid_indexed_address():
    probros.factor(0.001, probros.IndexedAddress("data", 0))


@probros.probabilistic_program
def test_restricted_observe_missing_expression():
    probros.factor()


@probros.probabilistic_program
def test_restricted_observe_additional_argument():
    probros.factor(0.123, "address", probros.Beta(0.1, 0.2))


@probros.probabilistic_program
def test_restricted_observe_valide_broadcasted(data):
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Broadcasted(probros.Normal(0, 1)),
        )


@probros.probabilistic_program
def test_restricted_sample_incorrect_broadcasted_arguments():
    for i in range(0, 100):
        _ = probros.sample(
            probros.IndexedAddress("i", i),
            probros.Broadcasted(probros.Normal(0, 1), 12),
        )


@probros.probabilistic_program
def test_restricted_sample_valid_iid(data):
    for i in range(0, 100):
        _ = probros.sample(
            probros.IndexedAddress("i", i),
            probros.IID(probros.Normal(0, 1), 12),
        )


@probros.probabilistic_program
def test_restricted_observe_incorrect_iid_missing_argument(data):
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress(data, i),
            probros.IID(probros.Normal(0, 1)),
        )


@probros.probabilistic_program
def test_restricted_indexed_address(data):
    return probros.sample(
        probros.IndexedAddress(":)", 21),
        probros.Normal(0, 1),
    )


@probros.probabilistic_program
def test_restricted_indexed_address_nested(data):
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


@probros.probabilistic_program
def test_restricted_indexed_address_missing_address(
    data,
):
    return probros.sample(probros.IndexedAddress(21), probros.Normal(0, 1))


@probros.probabilistic_program
def test_restricted_indexed_address_missing_number(data):
    return probros.sample(probros.IndexedAddress("i"), probros.Normal(0, 1))


@probros.probabilistic_program
class TestUnrecommendedUseCaseClass:
    pass


@probros.probabilistic_program
async def test_unrecommended_use_case_async_function():
    return "some promise"


message = "This file is not intended for execution"

if __name__ == f"__{'main'}__":
    raise RuntimeError(f"{message}!")

raise RuntimeError(message.rsplit(" ", 1)[0] + " usage!")
