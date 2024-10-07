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
# Test data generated with:
#   intercept~1
#   slope~0.5
xs = [0.93, 1.71, 2.61, 3.62, 4.12]
ys = [1.32, 2.00, 2.55, 2.39, 3.14]
__choicemap_aggregation(xs, ys)
(trace,) = importance_resampling(linear_regression_model, (xs, ys), __observe_constraints, 100000)
println("Inferred:")
println("\tgradient=$(trace["gradient"])")
println("\tintercept=$(trace["intercept"])")
