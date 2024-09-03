@probabilistic_program
def number_of_heads(probability):
    HEADS = 0
    TAILS = 1
    count = 0
    while True:
        cointoss = sample(
            IndexedAddress("cointoss", count),
            Bernoulli(probability),
        )
        if cointoss == TAILS:
            break
        count = count + 1
    return count
