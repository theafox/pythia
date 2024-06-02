import ast


def is_function_called(node: ast.AST, name: str) -> bool:
    """Check if the given node is a function call with the given name.

    This checks for both, direct function calls, i.e. `myname(...)`, and
    through attributes, i.e. `mypackage.myname(...)`.

    Args:
        node: The AST node to check.
        name: The name of the function to check for.

    Returns:
        bool: `True` if the node is a call to that specified function, `False`
        otherwise.
    """

    match node:
        case ast.Call(
            func=(ast.Name(id=called) | ast.Attribute(attr=called))
        ) if called == name:
            return True
        case _:
            return False


class Address:
    """A utility class for working with address-representations.

    This class is designed to be static encapsulation of address-related
    features and should not be instantiated.
    """

    # NOTE: extract this dynamically to future-proof for changes?
    _ADDRESS_CALL = "IndexedAddress"

    def __new__(cls):
        """Prevent instantiation of this class.

        Raises:
            RuntimeError: Always raised to prevent instantiation.
        """
        raise RuntimeError(f"{cls} is a static class.")

    @classmethod
    def is_address(cls, node: ast.AST) -> bool:
        """Check whether a given node is an address.

        Args:
            node: The AST node check

        Returns:
            `True` if the node represents an address, `False` otherwise.
        """

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
        """Get the string representation of the address type.

        Returns:
            The string representation of the address type.
        """
        return f"str | {cls._ADDRESS_CALL}(...)"


class Distribution:
    """A utility class for working with distribution-representations.

    This class is designed to be static encapsulation of address-related
    features and should not be instantiated.
    """

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
        """Prevent instantiation of this class.

        Raises:
            RuntimeError: Always raised to prevent instantiation.
        """
        raise RuntimeError(f"{cls} is a static class.")

    @classmethod
    def is_distribution(cls, node: ast.AST) -> bool:
        """Check whether a given node is an distribution.

        Args:
            node: The AST node check

        Returns:
            `True` if the node represents a distribution, `False` otherwise.
        """

        return any(
            is_function_called(node, distribution)
            for distribution in cls._DISTRIBUTIONS
        )

    @classmethod
    def representation(cls) -> str:
        """Get the string representation of the distribution type.

        Returns:
            The string representation of the distribution type.
        """
        return "distribution"
