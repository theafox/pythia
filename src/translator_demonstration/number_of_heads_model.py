# Own model.
@probabilistic_program
def number_of_heads_model(data):
    p = sample("p", Uniform(0, 1))
    count = 0
    while True:
        cointoss = sample(IndexedAddress("cointoss", count), Bernoulli(p))
        if cointoss == 1:
            break
        count = count + 1
    observe(data, "count", Dirac(count))
