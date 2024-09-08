@probabilistic_program
def model(n1, n2, k1, k2):
    # Prior on Single Rate Theta
    theta = sample("theta", Beta(1, 1))

    # Observed Counts
    observe(k1, "obs1", Binomial(n1, theta))
    observe(k2, "obs2", Binomial(n2, theta))

    # Posterior Predictive / generated quantities (correct?)
    postpredk1 = sample("postpredk1", Binomial(n1, theta))
    postpredk2 = sample("postpredk2", Binomial(n2, theta))

    return (postpredk1, postpredk2)
