# Translated code start.
using Gen
using Distributions
@gen function cointoss_model(data)
    probability = {"probability"} ~ uniform(0, 1)
    for i = 0:1:(length(data))-1
        if ((data[(i) + 1]) != (0)) && ((data[(i) + 1]) != (1))
            continue
        end
        {"$("data")[$(i)]"} ~ bernoulli(probability)
    end
end
__observe_constraints = Gen.choicemap()
function __choicemap_aggregation(data)
    for i = 0:1:(length(data))-1
        if ((data[(i) + 1]) != (0)) && ((data[(i) + 1]) != (1))
            continue
        end
        __observe_constraints["$("data")[$(i)]"] = data[(i) + 1]
    end
end
# Translated code end.
# Test data generated with:
#   p~0.7
data = [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1]
__choicemap_aggregation(data)
(trace,) = importance_resampling(cointoss_model, (data,), __observe_constraints, 100000)
println("Inferred:")
println("\tprobability=$(trace["probability"])")
