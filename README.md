# _PyThia_

This repository serves as the source code for the **Linter** and **Translator** discussed in the thesis _Specification and Translations of the Meta Probabilistic Programming Language PyThia_:

> There is a plethora of languages and frameworks available for writing probabilistic models.
> Each framework posses unique features, characteristics, and utilities, tailored to address a variety of use-cases.
> However, this diversity often hinders cross-platform compatibility and portability---especially in tasks such as benchmarking.
>
> To address these challenges, we propose a meta-language, _PyThia_, which aims to provide an overarching framework that abstracts away as much of these differences as possible while remaining expressive enough to accommodate a wide range model definitions.
> [...]
> To facilitate convenient usage of the meta-language, we developed and implemented a linter.
> Furthermore, we implemented a translator, which enables practical applications for _PyThia_ by facilitating the conversion of models written in the meta-language to various frameworks.
> [...]

Additionally, the evaluation of the translator and a predefined set of models is also included in this repository.
See [src/translator/test_translator/](/src/translator/test_translator/README.md) for more details.

For further details regarding the implementations and design choices, as well as discussions on the general architecture, refer to Chapters 4 and 5 in the aforementioned thesis.

## Requirements

- **Python** 3.12 or later,
- **pytest** (optional) for executing the automated tests, and
- any **Probabilistic Programming Language** (optional) for executing the translated models, e.g. [_Gen.jl_](https://github.com/probcomp/Gen.jl), [_Turing.jl_](https://github.com/TuringLang/Turing.jl), and [_Pyro_](https://github.com/pyro-ppl/pyro).

## Usage

Both implementations come modularized, but offer convenience scripts for executing them, `linter.py` and `translator.py` respectively.
That is to say, they may be executed like:

```sh
python src/linter.py [OPTIONS] <file>
```

```sh
python src/translator.py [OPTIONS] <translation-target> <file>
```

The available options for both implementations and a description on their functionality are available with the `-h` flag.
