@probabilistic_program
def rate_5_model(n1, n2, k1, k2):
    theta = sample("theta", Beta(1, 1))
    observe(k1, "obs1", Binomial(n1, theta))
    observe(k2, "obs2", Binomial(n2, theta))
    postpredk1 = sample("postpredk1", Binomial(n1, theta))
    postpredk2 = sample("postpredk2", Binomial(n2, theta))
    return (postpredk1, postpredk2)
