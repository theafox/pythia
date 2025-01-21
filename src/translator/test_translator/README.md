# Testing of the translator

The tests are done according to Chapter 6 of the thesis _Specifications and Translations of the Meta Probabilistic Programming Language PyThia_.

> The practical applicability of _PyThia_, as a meta-language, can be effectively demonstrated, and serve as a proof-of-concept of its practicability, through some translations.
> This chapter will present the results of translating and attempting inference with those translations for ten distinct models, curated to showcase the whole range of _PyThia_'s syntax.
> A comprehensive list of these models is provided in Appendix A.

Where the models in Appendix A may also be found in the folder `translator_demonstration/`.
The translated models may be found in their respective target-framework's folder, e.g. `test_translator/pyro/` or `test_translator/gen/`.

## Attempted Inference with Translated Models

The thesis also discusses attempted inference of those translated models.

> While we like syntactically successful translations of models, we have no guarantees that it can be used for inference.
> To address this limitation, all successfully translated models were subjected to testing using predefined test data and importance sampling as the inference method.

The predefined testing-data may be found in the [Jupyter](https://jupyter.org/) notebook `test_data.ipynb`.
Inference for all models may be attempted by executing the following bash command:

```bash
for file in src/translator/test_translator/{gen,pyro,turing}/*.(jl|py); \
    do echo "$file"; \
    [[ $file == *.py ]] \
        && python3 "$file" 2>/dev/null \
        || julia "$file" 2>/dev/null; \
    echo ""; \
done
```

Alternatively, the results of such an execution may be found in the file `test_results`.
