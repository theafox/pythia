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
        probros.observe(data[i], f"flip[{i}]", probros.Bernoulli(probability))
    return probability


# This should be validated, the deconstruction should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_deconstructor(data):
    mean, stddev = 2, 0.3
    probability = probros.Normal(mean, stddev)
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probability,
        )
    return probability


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
            probability = probros.sample(f"this[{i}]", probros.Uniform(0, 1))
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
        probability = probros.Poisson(0.7)
        for i in range(0, len(data)):
            probros.observe(
                data[i],
                probability.IndexedAddress("data", i),
                probability,
            )
        return probability

    @probros.probabilistic_program
    def invalid_probabilistic_program_in_function_fstring(data: list[float]):
        probability = probros.Poisson(0.2)
        for i in range(0, len(data)):
            probros.observe(
                data[i],
                f"data[{i}]",
                probability,
            )
        return probability


# This should be validated, the delete statement should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_delete(data):
    probability = probros.Uniform(0, 1)
    sum = 0
    for i in range(0, len(data)):
        probros.observe(
            data[i],
            probros.IndexedAddress("data", i),
            probability,
        )
        sum += data[i]
    del probability
    return sum


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
