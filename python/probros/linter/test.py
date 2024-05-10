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


# This should be validated, the f-string should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_fstring(data):
    probability = probros.sample("p", probros.Uniform(0, 1))
    for i in range(0, len(data)):
        probros.observe(data[i], f"flip[{i}]", probros.Bernoulli(probability))
    return probability


# This should be validated, the f-string should throw an error.
#
@probros.probabilistic_program
def invalid_probabilistic_program_nested(data):
    probability = probros.sample("p", probros.Uniform(0, 1))
    for i in range(0, len(data)):
        probros.observe(data[i], f"flip[{i}]", probros.Bernoulli(probability))

    @probros.probabilistic_program
    def invalidly_nested_probabilistic_program():
        return f"This will {'not'} be checked!"

    return probability


# This should not be validated.
#
def unchecked_duplicate_decorator(func):
    def wrapper(*args, **kwargs):
        func()
        func()

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


# This class method should be validated.
#
class ClassContainingProbabilisticProgram:
    @probros.probabilistic_program
    def valid_probabilistic_program_in_class(self):
        return

    @probros.probabilistic_program
    def invalid_probabilistic_program_in_class_fstring(self):
        return f"{'This is not valid!'}"


# This should be validated, the nested class should throw an error.
@probros.probabilistic_program
def invalid_probabilistic_program_nested_class():
    class invalidly_nested_class:
        pass


# This probabilistic_program nested inside of another function should be
# validated.
#
def outer_function():
    @probros.probabilistic_program
    def valid_probabilistic_program_in_function():
        return

    @probros.probabilistic_program
    def invalid_probabilistic_program_in_function_fstring():
        return f"{'This is not valid!'}"


# Give information that this is not the intended use-case.
#
@probros.probabilistic_program
class class_decorator:
    pass


# Give information that this is not the intended use-case.
#
@probros.probabilistic_program
async def invalid_probabilistic_program_async():
    pass


# This should not be validated.
#
if __name__ == f"__{'main'}__":
    pass
