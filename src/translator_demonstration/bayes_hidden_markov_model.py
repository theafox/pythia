# See: https://turinglang.org/docs/tutorials/04-hidden-markov-model/
@probabilistic_program
def bayes_hidden_markov_model(y, K):
    s = Vector(len(y), fill=0, t=int)  # State sequence.
    m = Vector(K, t=float)  # Emission matrix.
    T = Array((K, K), t=float)  # Transition matrix.
    for i in range(0, K):
        T[i, :] = sample(IndexedAddress("T", i), Dirichlet(1 / K, K))
        m[i] = sample(IndexedAddress("m", i), Normal(i + 1, 0.5))
    s[0] = sample(IndexedAddress("s", 0), DiscreteUniform(0, K - 1))
    observe(y[0], IndexedAddress("y", 0), Normal(m[s[0]], 0.1))
    for i in range(1, len(y)):
        s[i] = sample(IndexedAddress("s", i), Categorical(T[s[i - 1], :]))
        observe(y[i], IndexedAddress("y", i), Normal(m[s[i]], 0.1))
