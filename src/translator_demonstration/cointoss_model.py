# Own model.
@probabilistic_program
def cointoss_model(data):
    p = sample("p", Uniform(0, 1))
    for i in range(0, len(data)):
        if data[i] != 0 and data[i] != 1:
            continue
        observe(data[i], IndexedAddress("data", i), Bernoulli(p))
