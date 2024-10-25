# Own model.
@probabilistic_program
def cointoss_with_factor_model(data):
    p = sample("p", Uniform(0, 1))
    for i in range(0, len(data)):
        new = p
        if data[i] != 1:
            new = 1 - p
        factor(log(new), IndexedAddress("data", i))
    return p
