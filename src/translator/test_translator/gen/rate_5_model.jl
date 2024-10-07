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
# Test data generated with:
#   theta~0.6
n1 = 10
n2 = 15
k1 = 7
k2 = 8
__choicemap_aggregation(n1, n2, k1, k2)
(trace,) = importance_resampling(rate_5_model, (n1, n2, k1, k2), __observe_constraints, 100000)
println("Inferred:")
println("\ttheta=$(trace["theta"])")
