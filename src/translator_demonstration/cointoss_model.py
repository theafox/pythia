@probabilistic_program
def cointoss_model(data):
    probability = sample("probability", Uniform(0, 1))
    for i in range(0, len(data)):
        if data[i] != 0 and data[i] != 1:
            continue
        observe(data[i], IndexedAddress("data", i), Bernoulli(probability))
