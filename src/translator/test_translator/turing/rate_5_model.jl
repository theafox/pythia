# Translated code start.
using Turing
@model function rate_5_model(n1, n2, k1, k2)
    theta ~ Beta(1, 1)
    k1 ~ Binomial(n1, theta)
    k2 ~ Binomial(n2, theta)
    postpredk1 ~ Binomial(n1, theta)
    postpredk2 ~ Binomial(n2, theta)
    return (postpredk1, postpredk2)
end
# Translated code end.
# Test data generated with:
#   theta~0.6
n1 = 10
n2 = 15
k1 = 7
k2 = 8
display(sample(rate_5_model(n1, n2, k1, k2), NUTS(), 1000))
