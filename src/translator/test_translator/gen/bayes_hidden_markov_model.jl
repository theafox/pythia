# Translated code start.
using Gen
using Distributions
@gen function bayes_hidden_markov_model(y, K)
    s = fill(0, length(y))
    m = fill(0, K)
    T = fill(0, (K, K))
    for i = 0:1:(K)-1
        T[(i) + 1] = {"$("T")[$(i)]"} ~ dirichlet((1) / (K), K)
        m[(i) + 1] = {"$("m")[$(i)]"} ~ normal((i) + (1), 0.5)
    end
    s[(0) + 1] = {"$("s")[$(0)]"} ~ uniform_discrete(0, (K) - (1))
    {"$("y")[$(0)]"} ~ normal(m[(s[(0) + 1]) + 1], 0.1)
    for i = 1:1:(length(y))-1
        s[(i) + 1] = {"$("s")[$(i)]"} ~ uniform_discrete(0, (K) - (1))
        {"$("y")[$(i)]"} ~ normal(m[(s[(i) + 1]) + 1], 0.1)
    end
end
__observe_constraints = Gen.choicemap()
function __choicemap_aggregation(y, K)
    s = fill(0, length(y))
    m = fill(0, K)
    T = fill(0, (K, K))
    for i = 0:1:(K)-1
    end
    __observe_constraints["$("y")[$(0)]"] = y[(0) + 1]
    for i = 1:1:(length(y))-1
        __observe_constraints["$("y")[$(i)]"] = y[(i) + 1]
    end
end
# Translated code end.
# Test data generated with:
#   s~[2,5,9,5,6,4,9,4,3,0]
#   m~[1.17,2.30,2.44,4.63,4.73,4.99,6.01,7.80,9.74,11.03]
y = [2.49, 4.99, 10.95, 5.00, 5.88, 4.66, 10.97, 4.68, 4.44, 1.07]
K = 10
__choicemap_aggregation(y, K)
(trace,) = importance_resampling(bayes_hidden_markov_model, (y, K), __observe_constraints, 1000)
println("Inferred:")
println("\ts=[$(trace["s[0]"]), $(trace["s[1]"]), $(trace["s[2]"]), $(trace["s[3]"]), $(trace["s[4]"]), $(trace["s[5]"]), $(trace["s[6]"]), $(trace["s[7]"]), $(trace["s[8]"]), $(trace["s[9]"])]")
