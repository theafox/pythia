# Translated code start.
using Gen
using Distributions
@gen function linear_regression_model(xs, ys)
    gradient = {"gradient"} ~ normal(0, 10)
    intercept = {"intercept"} ~ normal(0, 10)
    for i = 0:1:(min(length(xs), length(ys)))-1
        {"$("ys")[$(i)]"} ~ normal(((gradient) * (xs[(i) + 1])) + (intercept), 1)
    end
end
__observe_constraints = Gen.choicemap()
function __choicemap_aggregation(xs, ys)
    for i = 0:1:(min(length(xs), length(ys)))-1
        __observe_constraints["$("ys")[$(i)]"] = ys[(i) + 1]
    end
end
# Translated code end.
using Random
# Test data.
xs = [ 1,  2,  3,  4,  5,  6,  7,  8,  9, 10 ]
ys = [ 1.8528, 2.0800, 2.6957, 3.4482, 3.8735, 3.8045, 4.6900, 4.9697, 5.4794,
       6.0821 ]
model = linear_regression_model
arguments = (xs, ys)
addresses = ("gradient", "intercept")
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
