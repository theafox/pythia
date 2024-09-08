r"""A translator for probabilistic programs.

This module provides a general purpose translator class which may be used with
custom mappings for a spectrum of use-cases. Default implementations and a
CLI-interface are provided which may be used to translate code conforming to
the specifications of the PyThia Meta-Probabilistic-Programming-Language into
the frameworks Gen, Turing, and Pyro.

Usage:
    This module provides default implementations for different languages and
    frameworks. Moreover, the `Translator` class may be used to translate
    custom code with custom mappings.

Attributes:
    Translator: This class represents a general translator. By specifying
        mappings and other potential dependencies, the translator may be suited
        to the required use-case.
    default_julia_translator: This provides the default translator for the
        Julia programming language. However, more specific aspects requiring
        knowledge about target frameworks are missing.
    default_gen_translator: This provides the default translator for the Gen
        framework.
    default_turing_translator: This provides the default translator for the
        Turing framework.
    default_python_translator: This provides the default translator for the
        Python programming language. However, more specific aspects requiring
        knowledge about target frameworks are missing.
    default_pyro_translator: This provides the default translator for the Pyro
        framework.
    ExitCode: An enumeration representing the different possible exit codes.
    Context: A class representing translation context used during the
        translation process.

Examples:
    ```py
    tree = ast.parse(code)
    translator = default_gen_translator()
    translation = translator.translate(tree)
    ```

Author: T. Kaufmann <e12002221@student.tuwien.ac.at>
Version: 0.1.0
Status: In Development
"""

from .context import *
from .main import *
