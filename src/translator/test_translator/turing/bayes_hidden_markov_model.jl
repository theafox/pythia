# Translated code start.
using Turing
@model function bayes_hidden_markov_model(y, K)
    s = fill(0, length(y))
    m = fill(0, K)
    T = fill(0, (K, K))
    for i = 0:1:(K)-1
        T[(i) + 1] ~ Dirichlet(K, (1) / (K))
        m[(i) + 1] ~ Normal((i) + (1), 0.5)
    end
    s[(0) + 1] ~ DiscreteUniform(0, (K) - (1))
    # y[(0) + 1] ~ Normal(m[(s[(0) + 1]) + 1], 0.1)  # float indexing is not allowed.
    y[(0) + 1] ~ Normal(m[(trunc(Int, s[(0) + 1])) + 1], 0.1)
    for i = 1:1:(length(y))-1
        s[(i) + 1] ~ DiscreteUniform(0, (K) - (1))
        # y[(i) + 1] ~ Normal(m[(s[(i) + 1]) + 1], 0.1)  # float indexing is not allowed.
        y[(i) + 1] ~ Normal(m[(trunc(Int, s[(i) + 1])) + 1], 0.1)
    end
end
# Translated code end.
# Test data generated with:
#   s~[2,5,9,5,6,4,9,4,3,0]
#   m~[1.17,2.30,2.44,4.63,4.73,4.99,6.01,7.80,9.74,11.03]
y = [2.49, 4.99, 10.95, 5.00, 5.88, 4.66, 10.97, 4.68, 4.44, 1.07]
K = 10
display(sample(bayes_hidden_markov_model(y, K), NUTS(), 1000))
