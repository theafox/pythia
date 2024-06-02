import ast


def is_function_called(node: ast.AST, name: str) -> bool:
    match node:
        case ast.Call(
            func=(ast.Name(id=called) | ast.Attribute(attr=called))
        ) if called == name:
            return True
        case _:
            return False


class Address:

    # NOTE: extract this dynamically to future-proof for changes?
    _ADDRESS_CALL = "IndexedAddress"

    def __new__(cls):
        raise RuntimeError(f"{cls} is a static class.")

    @classmethod
    def is_address(cls, node: ast.AST) -> bool:
        match node:
            case ast.Constant(value=str()):
                return True
            case ast.Call(
                func=(ast.Name(id=called) | ast.Attribute(attr=called))
            ) if called == cls._ADDRESS_CALL:
                return True
            case _:
                return False

    @classmethod
    def representation(cls) -> str:
        return f"str | {cls._ADDRESS_CALL}(...)"


class Distribution:

    # NOTE: extract this dynamically to future-proof for changes?
    _DISTRIBUTIONS = [
        "IID",
        "Broadcasted",
        "Dirac",
        "Beta",
        "Cauchy",
        "Exponential",
        "Gamma",
        "HalfCauchy",
        "HalfNormal",
        "InverseGamma",
        "Normal",
        "StudentT",
        "Uniform",
        "Bernoulli",
        "Binomial",
        "DiscreteUniform",
        "Geometric",
        "HyperGeometric",
        "Poisson",
        "Dirichlet",
        "MultivariateNormal",
    ]

    def __new__(cls):
        raise RuntimeError(f"{cls} is a static class.")

    @classmethod
    def is_distribution(cls, node: ast.AST) -> bool:
        return any(
            is_function_called(node, distribution)
            for distribution in cls._DISTRIBUTIONS
        )

    @classmethod
    def representation(cls) -> str:
        return "distribution"
