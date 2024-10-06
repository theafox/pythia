@probabilistic_program
def cointoss_with_factor_model(data):
    probability = sample("probability", Uniform(0, 1))
    for i in range(0, len(data)):
        new = probability
        if data[i] != 1:
            new = 1 - probability
        factor(log(new), IndexedAddress("data", i))
    return probability
