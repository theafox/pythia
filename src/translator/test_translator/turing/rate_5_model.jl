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
# Test data.
n1 = 50
n2 = 75
k1 = 30
k2 = 43
model = rate_5_model
arguments = (n1, n2, k1, k2)
addresses = ("theta",)
# Inference.
Turing.Random.seed!(0)
inferred = sample(model(arguments...), IS(), 10_000, progress=false)
println("Inferred:")
weights = exp.(inferred[:lp])
weights = weights / sum(weights)
for address in addresses
    mean = sum(inferred[address] .* weights)
    println(" - $address=$mean")
end
