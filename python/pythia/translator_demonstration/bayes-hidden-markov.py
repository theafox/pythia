@probabilistic_program
def bayes_hidden_markov_model(y, K):
    s = Vector(len(y), fill=0)  # State sequence.
    m = Vector(K)  # Emission matrix.
    T = Array((K, K))  # Transition matrix.

    # Assign distributions to each element of the transition matrix and the
    # emission matrix.
    for i in range(0, K):
        T[i] = sample(IndexedAddress("T", i), IID(Dirichlet(1 / K), K))
        m[i] = sample(IndexedAddress("m", i), Normal(i + 1, 0.5))

    # Observe each point of the input.
    s[0] = DiscreteUniform(0, K)
    observe(y[0], IndexedAddress("y", 0), Normal(m[s[0]], 0.1))

    for i in range(1, len(y)):
        s[i] = DiscreteUniform(0, K)
        observe(y[i], IndexedAddress("y", i), Normal(m[s[i]], 0.1))
