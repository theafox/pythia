@probabilistic_program
def number_of_heads_model(data):
    probability = sample("probability", Uniform(0, 1))
    count = 0
    while True:
        cointoss = sample(
            IndexedAddress("cointoss", count),
            Bernoulli(probability),
        )
        if cointoss == 1:
            break
        count = count + 1
    observe(data, "count", Dirac(count))
