# type: ignore
import probros


# This should be validated, no errors should occur.
#
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


# This should raise a warning about an unidentifiable decorator.
#
@1 + 1
def unverifiable_function_add_decorator():
    pass


# This should raise a warning about an unidentifiable decorator.
#
@"hello decorator!"
def unverifiable_function_string_decorator():
    pass


# This should raise a warning about an unidentifiable decorator.
#
@"probabilistic_program"
def unverifiable_function_string_decorator_probabilistic_program():
    pass


# This should be validated, the f-string should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_fstring(data):
    probability = probros.sample("p", probros.Uniform(0, 1))
    for i in range(0, len(data)):
        address = f"flip[{i}]"
        probros.observe(data[i], address, probros.Bernoulli(probability))
    return probability


# This should be validated, the deconstruction should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_deconstructor(data):
    mean, stddev = 2, 0.3
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Normal(mean, stddev),
        )


# This should be validated, the nested function should throw an error.
#
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


# This should not be validated.
#
def unchecked_duplicate_decorator(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        func(*args, **kwargs)

    return wrapper


# This should not be validated.
#
@unchecked_duplicate_decorator
def unchecked_function():
    VAR = f"This should {'allow'} anything!"

    def unchecked_nested_function(arg: str) -> str:
        return f"{arg=} including f-strings"

    VAR += "\nand nested functions"
    return unchecked_nested_function(VAR)


# Class methods which are annotated as probabilistic programs should be
# validated.
#
class ClassContainingProbabilisticProgram:

    # This should be validated, no errors should occur.
    #
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

    # This should be validated, the f-string should throw an error.
    #
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


# This should be validated, the nested class should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_nested_class():
    class InvalidlyNestedClass:
        pi = 3

    return InvalidNestedClass.pi


# This probabilistic_program nested inside of another function should be
# validated.
#
def outer_function():
    @probros.probabilistic_program
    def valid_probabilistic_program_in_function(data: list[int]):
        for i in range(0, len(data)):
            probros.observe(
                data[i],
                probros.IndexedAddress("data", i),
                probros.Poisson(0.7),
            )

    @probros.probabilistic_program
    def invalid_probabilistic_program_in_function_fstring(data: list[float]):
        for i in range(0, len(data)):
            address = f"data[{i}]"
            probros.observe(
                data[i],
                address,
                probros.Poisson(0.2),
            )


# This should be validated, the delete statement should throw an error.
#
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


# This should be validated, type aliasing should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_type_aliasing():
    type Probabilities = list[probros.Beta]
    probability: Probabilities = []
    for i in range(0, 5):
        probability += probros.Beta(0.1, 0.5)
    return probability


# This should be validated, asynchrony should throw an error.
#
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


# This should be validated, with-statements should throw an error.
#
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


# This should be validated, with-statements should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_with_variables(generator):
    with generator() as data:
        for i in range(0, len(data)):
            probros.observe(
                data[i],
                probros.IndexedAddress("data", i),
                probros.Uniform(0, 1),
            )


# This should be validated, for-loops not using `range` should throw an error.
#
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


# This should be validated, for-loops not using `range` should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_for_constant(data):
    step = 0
    for _ in "this shouldn't work either!":
        probros.observe(data[step], "hi!", probros.Uniform(0, 1))
        step += 1


# This should be validated, the walrus operator should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_walrus_operator(data):
    if (length := len(data)) > 10:
        for i in range(0, length):
            probros.observe(
                data[i],
                probros.IndexedAddress("data", i),
                probros.Uniform(0, 1),
            )


# This should be validated, the shift operators should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_shift_operator(n):
    return 1 << n


# This should be validated, the shift operators should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_bitwise_operator(a, b, c, d):
    result = a & b
    result = result | c
    result = result ^ d
    return result


# This should be validated, the bitwise complement `~` should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_bitwise_complement(n):
    return ~n


# This should be validated, the lambda expression should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_lambda(data):
    data = filter(lambda point: point >= 0, data)
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Gamma(0.1, 0.5),
        )


# This should be validated, the inline if expression should throw an error.
#
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


# This should be validated, the walrus operator should throw an error.
#
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


# This should be validated, sets should be prohibited.
#
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


# This should be validated, comprehensions and generators should throw an
# error.
@probros.probabilistic_program
def invalid_probabilistic_program_list_comprehension():
    return [2**n for n in range(10)]


# This should be validated, comprehensions and generators should throw an
# error.
@probros.probabilistic_program
def invalid_probabilistic_program_set_comprehension():
    return {2**n for n in range(10)}


# This should be validated, comprehensions and generators should throw an
# error.
@probros.probabilistic_program
def invalid_probabilistic_program_dictionary_comprehension():
    return {n: 2**n for n in range(10)}


# This should be validated, comprehensions and generators should throw an
# error.
@probros.probabilistic_program
def invalid_probabilistic_program_generator():
    return sum(2**n for n in range(10))


# This should be validated, asynchrony should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_asynchronous_await(data):
    probabilities = (
        await invalid_probabilistic_program_asynchronous_generator()
    )
    for i in range(0, len(probabilities)):
        if probabilities[i] > 0.9:
            return True
    return False


# This should be validated, asynchrony should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_asynchronous_generator():
    return [probros.Normal(n, n * 0.1) async for n in range(10)]


# This should be validated, yield expressions should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_yield(data):
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Uniform(0, 1),
        )
        yield data[i]


# This should be validated, yield expressions should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_yield_from(data):
    yield from invalid_probabilistic_program_yield(data)


# This should be validated, the starred variable should throw an error.
#
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


# This should be validated, the slice should throw an error.
#
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


# This should be validated, this should not throw an error.
#
@probros.probabilistic_program
def valid_probabilistic_program_array_assign(data):
    details = list()
    details[0] = data
    details[1] = sum(data)
    details[2] = len(data)
    details[3] = details[1] / details[2]
    return details


# This should be validated, the attribute assign should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_attribute_assign(data):
    data.sum = sum(data)
    return data.sum


@probros.probabilistic_program
def valid_probabilistic_program_standalone_expression_observe_call():
    probros.observe(
        12,
        "standalone_observe_call",
        probros.Uniform(0, 1),
    )


@probros.probabilistic_program
def valid_probabilistic_program_standalone_expression_factor_call():
    probros.factor(0.0124)


@probros.probabilistic_program
def invalid_probabilistic_program_standalone_expression_function_call(n):
    initialize_context()


@probros.probabilistic_program
def invalid_probabilistic_program_standalone_expression_calculation(n):
    1 + 2**3 / 4 // 5


# This should be validated, the subscript assign should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_subscript(data):
    data[0, -1] = data[-1], data[0]
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Dirac(0.25),
        )


# This should be validated, the observe-call should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_observe_number_address(data):
    probability = probros.sample("p", probros.Uniform(0, 1))
    for i in range(0, len(data)):
        probros.observe(data[i], 123, probros.Bernoulli(probability))
    return probability


# This should be validated, the observe-call should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_observe_variable_address(data: list[float]):
    for i in range(0, len(data)):
        address = probros.IndexedAddress("data", i)
        probros.observe(
            data[i],
            address,
            probros.Poisson(0.2),
        )


# This should be validated, no errors should occur.
#
@probros.probabilistic_program
def valid_probabilistic_program_observe_keyword_arguments(data: list[float]):
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            distribution=probros.Poisson(0.2),
            address=probros.IndexedAddress("data", i),
        )


# This should be validated, no errors should occur.
#
@probros.probabilistic_program
def valid_probabilistic_program_observe_keyword_argument(data: list[float]):
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            distribution=probros.Poisson(0.2),
        )


# This should be validated, the incorrect observation argument order should
# throw an error.
#
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


# This should be validated, the missing positional observation argument should
# throw an error.
#
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


# This should be validated, no errors should occur.
#
@probros.probabilistic_program
def valid_probabilistic_program_sample(data: list[float]):
    return sample("p", probros.Dirac(True))


# This should be validated, the sample call should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_sample_incorrect_address_number(
    data: list[float],
):
    return probros.sample(123, probros.Dirac(True))


# This should be validated, the sample call should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_sample_missing_argument(
    data: list[float],
):
    return probros.sample("p")


# This should be validated, the sample call should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_sample_keyword_argument(
    data: list[float],
):
    return probros.sample("p", distribution=probros.Uniform(0, 1))


@probros.probabilistic_program
def valid_probabilistic_program_factor_string_address():
    probros.factor(0.001, address="data")


@probros.probabilistic_program
def valid_probabilistic_program_factor_indexed_address():
    probros.factor(0.001, probros.IndexedAddress("data", 0))


@probros.probabilistic_program
def invalid_probabilistic_program_factor_missing_expression():
    probros.factor()


@probros.probabilistic_program
def invalid_probabilistic_program_factor_additional_arguments():
    probros.factor(0.123, "address", probros.Beta(0.1, 0.2))


# This should be validated, no errors should occur.
#
@probros.probabilistic_program
def valid_probabilistic_program_broadcast_statement(data):
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probros.Broadcasted(probros.Normal(0, 1)),
        )


# This should be validated, the invalid `Broadcasted` call should throw an
# error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_broadcast_statement_constant():
    for i in range(0, 100):
        _ = probros.sample(
            probros.IndexedAddress("i", i),
            probros.Broadcasted(probros.Normal(0, 1), 12),
        )


# This should be validated, no errors should occur.
#
@probros.probabilistic_program
def valid_probabilistic_program_iid_statement(data):
    for i in range(0, 100):
        _ = probros.sample(
            probros.IndexedAddress("i", i),
            probros.IID(probros.Normal(0, 1), 12),
        )


# This should be validated, the invalid `IID` call should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_iid_statement_missing_constant(data):
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress(data, i),
            probros.IID(probros.Normal(0, 1)),
        )


@probros.probabilistic_program
def valid_probabilistic_program_indexed_address(data):
    return probros.sample(
        probros.IndexedAddress(":)", 21),
        probros.Normal(0, 1),
    )


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


@probros.probabilistic_program
def invalid_probabilistic_program_invalid_indexed_address_call_no_address(
    data,
):
    return probros.sample(probros.IndexedAddress(21), probros.Normal(0, 1))


@probros.probabilistic_program
def invalid_probabilistic_program_invalid_indexed_address_call_no_number(data):
    return probros.sample(probros.IndexedAddress("i"), probros.Normal(0, 1))


# This may give information that this is not the intended use-case.
#
@probros.probabilistic_program
class UnrecommendedProbabilisticProgramDecoratorOnClass:
    pass


# This may give information that this is not the intended use-case.
#
@probros.probabilistic_program
async def unrecommended_probabilistic_program_decorator_on_async_function():
    return "some promise"


# Nothing of the following should be be validated.
#
message = "This file is not intended for execution"

if __name__ == f"__{'main'}__":
    raise RuntimeError(f"{message}!")

raise RuntimeError(message.rsplit(" ", 1)[0] + " usage!")
