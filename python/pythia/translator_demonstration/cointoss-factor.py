@probabilistic_program
def coinflip_with_factor(data):
    probability = sample("probability", Uniform(0, 1))
    for i in range(0, len(data)):
        new = probability
        if data[i] != 1:
            new = 1 - probability
        factor(math.log(new))
    return probability
