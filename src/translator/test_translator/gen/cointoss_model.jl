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
using Random
# Test data.
data = [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1]
model = cointoss_model
arguments = (data,)
addresses = ("probability",)
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
