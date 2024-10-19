# Translated code start.
using Gen
using Distributions
@gen function rate_5_model(n1, n2, k1, k2)
    theta = {"theta"} ~ beta(1, 1)
    {"obs1"} ~ binom(n1, theta)
    {"obs2"} ~ binom(n2, theta)
    postpredk1 = {"postpredk1"} ~ binom(n1, theta)
    postpredk2 = {"postpredk2"} ~ binom(n2, theta)
    return (postpredk1, postpredk2)
end
__observe_constraints = Gen.choicemap()
function __choicemap_aggregation(n1, n2, k1, k2)
    __observe_constraints["obs1"] = k1
    __observe_constraints["obs2"] = k2
    return
end
# Translated code end.
using Random
# Test data.
n1 = 50
n2 = 75
k1 = 30
k2 = 43
model = rate_5_model
arguments = (n1, n2, k1, k2)
addresses = ("theta",)
# Inference.
Random.seed!(0)
__choicemap_aggregation(arguments...)
(traces, log_weights) = importance_sampling(model, arguments,
                                            __observe_constraints, 10_000)
println("Inferred:")
weights = exp.(log_weights)
weights = weights / sum(weights)
for address in addresses
    mean = sum([trace[address] for trace in traces] .* weights)
    println(" - $address=$mean")
end
