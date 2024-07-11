from translator import (
    Translator,
    default_julia_translator,
    default_python_translator,
)


def test(
    julia_translator: Translator,
    python_translator: Translator,
    code: str,
) -> None:
    print("\n\n==================== original code ====================\n")
    print(code)
    print("\n=====> translated to julia:\n")
    julia_code = julia_translator.translate_code(code)
    print(julia_code)
    print("\n=====> translated to python:\n")
    python_code = python_translator.translate_code(code)
    print(python_code)


if __name__ == "__main__":
    code_pieces = [
        """\
@pr.probabilistic_program
def coin_flips(data):
    p = pr.sample("p", pr.Uniform(0, 1))
    for i in range(len(data)):
        pr.observe(data[i], pr.IndexedAddress("flip", i), pr.Bernoulli(p))
    p = None
    return p
        """,
        """\
@pr.probabilistic_program
def geometric(p: float):
    i = 0
    while True:
        b = pr.sample(pr.IndexedAddress("b",i), pr.Bernoulli(p))
        if not b != 1 and True and False:
            break
        elif a == 0:
            continue
        else:
            x = '"hello" world with 100$'
            y = (1,)
            z = [2,probros.sample(1)]
            a = z[1]
        i = i + 1
    return i
        """,
        "a = None + False <= None and True",
    ]

    julia_translator = default_julia_translator()
    python_translator = default_python_translator()
    for code in code_pieces:
        test(julia_translator, python_translator, code)
